import requests
from webvirtcloud.celery import app

from compute.helper import assign_free_compute
from network.helper import (
    assign_free_ipv4_public,
    assign_free_ipv4_compute,
    assign_free_ipv4_private, 
)
from models.models import Compute
from network.models import Network, IPAddress
from .models import Virtance


@app.task
def create_virtance(virtance_id):
    compute = None
    ipv4_public = None
    ipv4_compute = None
    ipv4_private = None
    virtance = Virtance.objects.get(id=virtance_id)

    if assign_free_compute(virtance.id) is True:
        compute = Compute.objects.get(id=virtance.compute.id)

    if assign_free_ipv4_compute(virtance.id) is True:
        ipv4_compute = IPAddress.objects.get(network__type=Network.COMPUTE, virtance=virtance)

    if assign_free_ipv4_public(virtance.id) is True:
        ipv4_public = IPAddress.objects.get(network__type=Network.PUBLIC, virtance=virtance)

    if assign_free_ipv4_private(virtance.id) is True:
        ipv4_private = IPAddress.objects.get(network__type=Network.PRIVATE, virtance=virtance)

    if compute and ipv4_public and ipv4_compute and ipv4_private:
        pass
