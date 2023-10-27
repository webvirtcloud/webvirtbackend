from ipaddress import IPv4Network
from webvirtcloud.celery import app

from compute.webvirt import WebVirtCompute
from virtance.utils import virtance_error
from .models import FloatIP
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
        virtance_error(virtance_id, res.get("detail"), "assign_floating_ip")
    else:
        virtance.reset_event()
        floatip.reset_event()


@app.task
def unassign_floating_ip(floating_ip_id):
    pass


@app.task
def delete_floating_ip(floating_ip_id):
    pass
