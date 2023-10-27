from ipaddress import IPv4Network
from django.utils import timezone

from webvirtcloud.celery import app
from compute.webvirt import WebVirtCompute
from virtance.utils import virtance_error
from .models import FloatIP, FloatIPCounter
from network.models import Network, IPAddress
from virtance.models import Virtance



@app.task
def assign_floating_ip(floating_ip_id, virtance_id):
    floatip = FloatIP.objects.get(id=floating_ip_id)
    virtance = Virtance.objects.get(id=virtance_id)
    ipv4_float = IPAddress.objects.get(id=floatip.ipaddress.id)
    ipv4_compute = IPAddress.objects.filter(virtance=virtance, network__type=Network.COMPUTE).first()

    floatip.event = FloatIP.ASSIGN
    floatip.save()
    
    wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
    ipv4_compute_prefix = IPv4Network(f"{ipv4_float.address}/{ipv4_float.network.netmask}", strict=False).prefixlen
    res = wvcomp.float_ip_assign(
        ipv4_compute.address, ipv4_float.address, ipv4_compute_prefix, ipv4_float.network.gateway
    )
    if isinstance(res, dict) and res.get("detail"):
        virtance_error(virtance.id, res.get("detail"), "assign_floating_ip")
    else:
        virtance.reset_event()
        floatip.reset_event()


@app.task
def unassign_floating_ip(floating_ip_id):
    floatip = FloatIP.objects.get(id=floating_ip_id)
    virtance = floatip.ipaddress.virtance
    ipv4_float = IPAddress.objects.get(id=floatip.ipaddress.id)
    ipv4_compute = IPAddress.objects.filter(virtance=virtance, network__type=Network.COMPUTE).first()
    
    wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
    ipv4_compute_prefix = IPv4Network(f"{ipv4_float.address}/{ipv4_float.network.netmask}", strict=False).prefixlen
    res = wvcomp.float_ip_unassign(
        ipv4_compute.address, ipv4_float.address, ipv4_compute_prefix, ipv4_float.network.gateway
    )
    if isinstance(res, dict) and res.get("detail"):
        virtance_error(virtance.id, res.get("detail"), "unassign_floating_ip")
    else:
        virtance.reset_event()
        floatip.reset_event()

        ipaddress = floatip.ipaddress
        ipaddress.virtance = None
        ipaddress.save()


@app.task
def delete_floating_ip(floating_ip_id):
    floatip = FloatIP.objects.get(id=floating_ip_id)
    virtance = floatip.ipaddress.virtance
    floatip_counter = FloatIPCounter.objects.get(floatip=floatip)
    ipv4_float = IPAddress.objects.get(id=floatip.ipaddress.id)
    ipv4_compute = IPAddress.objects.filter(virtance=virtance, network__type=Network.COMPUTE).first()
    
    if floatip.ipaddress.virtance:
        virtance = floatip.ipaddress.virtance
        virtance.event = Virtance.UNASSIGN_FLOATING_IP
        virtance.save()

        wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
        ipv4_compute_prefix = IPv4Network(f"{ipv4_float.address}/{ipv4_float.network.netmask}", strict=False).prefixlen
        res = wvcomp.float_ip_unassign(
            ipv4_compute.address, ipv4_float.address, ipv4_compute_prefix, ipv4_float.network.gateway
        )
        if isinstance(res, dict) and res.get("detail"):
            virtance_error(virtance.id, res.get("detail"), "delete_floating_ip")
        else:
            ipaddress = floatip.ipaddress
            virtance.reset_event()

            floatip.delete()

            ipaddress.delete()

            current_time = timezone.now()
            first_day_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            try:
                floatip_counter = FloatIPCounter.objects.get(started__gt=first_day_month, floatip=floatip)
            except FloatIPCounter.DoesNotExist:
                floatip_counter = FloatIPCounter.objects.create(
                    floatip=floatip,
                    amount=0.0,
                    started=current_time - timezone.timedelta(hours=1),
                )
            floatip_counter.stop()
