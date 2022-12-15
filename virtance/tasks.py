from webvirtcloud.celery import app

from compute.helper import assign_free_compute
from network.helper import (
    assign_free_ipv4_compute, 
    assign_free_ipv4_private, 
    assign_free_ipv4_public
)
from .models import Virtance


@app.task
def create_virtance(virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)

    if assign_free_compute(virtance_id) is True:
        pass
