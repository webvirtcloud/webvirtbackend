from webvirtcloud.celery import app
from compute.webvirt import WebVirtCompute

from compute.models import Compute
from virtance.models import Virtance
from .models import Image
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
                    image_error(
                        image.id, f'Region: {region}, Error:{res.get("detail")}', f"delete_image_{image.type}"
                    )

        if image.regions.count() == 0:
            image.delete()
