from webvirtcloud.celery import app

from .models import LBaaS
from virtance.tasks import create_virtance


@app.task
def create_lbaas(lbaas_id):
    lbaas = LBaaS.objects.get(id=lbaas_id)

    if create_virtance(lbaas.virtance.id, send_email=False):
        pass
