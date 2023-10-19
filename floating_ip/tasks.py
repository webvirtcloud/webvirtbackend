from webvirtcloud.celery import app

from .models import FloatIP, FloatIPCounter
from virtance.models import Virtance
from network.helper import assign_free_ipv4_public


@app.task
def assign_floating_ip(virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)
    
    ipaddress_id = assign_free_ipv4_public(virtance.id, is_float=True)
    if ipaddress_id:
        floatip = FloatIP.objects.create(user=virtance.user, ipaddress_id=ipaddress_id)
        FloatIPCounter.objects.create(floatip=floatip, amount=0.0)
