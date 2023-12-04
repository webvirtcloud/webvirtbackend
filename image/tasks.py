from decimal import Decimal
from django.utils import timezone

from webvirtcloud.celery import app
from compute.webvirt import WebVirtCompute
from compute.models import Compute
from .models import Image, SnapshotCounter
from .utils import image_error


@app.task
def image_delete(image_id):
    image = Image.objects.get(pk=image_id)
    image.event = Image.DELETE
    image.save()

    if image.type == Image.SNAPSHOT or image.type == Image.BACKUP:
        for region in image.regions.all():
            computes = Compute.objects.filter(region=region, is_active=True, is_deleted=False).order_by("?")
            for compute in computes:
                wvcomp = WebVirtCompute(compute.token, compute.hostname)
                res = wvcomp.get_storages()
                if res.get("detail") is None:
                    for storage in res.get("storages"):
                        res = wvcomp.get_storage(storage.get("name"))
                        if res.get("detail") is None:
                            storage = res.get("storage")
                            for vol in storage.get("volumes"):
                                if vol.get("name") == image.file_name:
                                    res = wvcomp.delete_storage_volume(storage.get("name"), vol.get("name"))
                                    if res.get("detail") is None:
                                        image.regions.remove(region)
                                        break
                if res.get("detail"):
                    image_error(image.id, f'Region: {region}, Error:{res.get("detail")}', f"delete_image_{image.type}")
                    return False

        if image.regions.count() == 0:
            image.delete()

    return True


@app.task
def snapshot_counter():
    current_time = timezone.now()
    current_day = current_time.day
    current_hour = current_time.hour
    first_day_current_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    for image in Image.objects.filter(type=Image.SNAPSHOT, is_deleted=False):
        try:
            SnapshotCounter.objects.get(started__gt=first_day_current_month, image=image)
        except SnapshotCounter.DoesNotExist:
            period_start = current_time - timezone.timedelta(hours=1)
            SnapshotCounter.objects.create(image=image, amount=0.0, started=period_start)

    snapshot_counters = SnapshotCounter.objects.filter(started__gt=first_day_current_month, stopped__isnull=True)

    if current_day == 1 and current_hour == 0:
        previous_month = current_time - timezone.timedelta(days=1)
        period_end = previous_month.replace(hour=23, minute=59, second=59, microsecond=999999)
        snapshot_counters.update(stopped=period_end)
    else:
        for snap_count in snapshot_counters:
            snap_count.amount += Decimal(0.0)
            snap_count.save()
