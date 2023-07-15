from webvirtcloud.celery import app
from compute.webvirt import WebVirtCompute

from compute.models import Compute
from .models import Image
from .utils import image_error


@app.task
def image_delete(image_id):
    image = Image.objects.get(pk=image_id)
    
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
                            for vol in res.get("volumes"):
                                if vol.get("name") == image.file_name:
                                    res = wvcomp.delete_storage_volume(storage.get("name"), vol.get("name"))
                                    if res.get("detail") is None:
                                        image.regions.remove(region)
                                        break
                if res.get("detail"):
                    image_error(image.id, res.get("detail"), f"delete_{image.type}_image")

        if image.regions.count() == 0:
            image.delete()
