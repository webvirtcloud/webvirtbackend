from decimal import Decimal
from ipaddress import IPv4Network
from django.utils import timezone

from webvirtcloud.celery import app
from compute.webvirt import WebVirtCompute
from virtance.utils import virtance_error
from .utils import floatip_error
from .models import FloatIP, FloatIPCounter
from network.models import Network, IPAddress
from virtance.models import Virtance


@app.task
def assign_floating_ip(floating_ip_id, virtance_id):
    floatip = FloatIP.objects.get(id=floating_ip_id)
    virtance = Virtance.objects.get(id=virtance_id)
    ipaddress = floatip.ipaddress
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
        floatip_error(floatip.id, res.get("detail"), "assign_floating_ip")
        virtance_error(virtance.id, res.get("detail"), "assign_floating_ip")
    else:
        if ipaddress.virtance is None:
            ipaddress.virtance = virtance
            ipaddress.save()

        virtance.reset_event()
        floatip.reset_event()


@app.task
def unassign_floating_ip(floating_ip_id, virtance_reset_event=True):
    floatip = FloatIP.objects.get(id=floating_ip_id)
    virtance = floatip.ipaddress.virtance
    ipaddress = floatip.ipaddress
    ipv4_float = IPAddress.objects.get(id=floatip.ipaddress.id)
    ipv4_compute = IPAddress.objects.filter(virtance=virtance, network__type=Network.COMPUTE).first()

    wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
    ipv4_compute_prefix = IPv4Network(f"{ipv4_float.address}/{ipv4_float.network.netmask}", strict=False).prefixlen
    res = wvcomp.float_ip_unassign(
        ipv4_compute.address, ipv4_float.address, ipv4_compute_prefix, ipv4_float.network.gateway
    )
    if isinstance(res, dict) and res.get("detail"):
        floatip_error(floatip.id, res.get("detail"), "unassign_floating_ip")
        virtance_error(virtance.id, res.get("detail"), "unassign_floating_ip")
    else:
        ipaddress.virtance = None
        ipaddress.save()

        if virtance_reset_event is True:
            virtance.reset_event()
        floatip.reset_event()


@app.task
def reassign_floating_ip(floating_ip_id, virtance_id):
    floatip = FloatIP.objects.get(id=floating_ip_id)
    ipaddress = floatip.ipaddress
    virtance_old = floatip.ipaddress.virtance
    virtance_new = Virtance.objects.get(id=virtance_id)
    ipv4_float = IPAddress.objects.get(id=floatip.ipaddress.id)

    floatip.event = FloatIP.UNASSIGN
    floatip.save()

    virtance_old.event = Virtance.UNASSIGN_FLOATING_IP
    virtance_old.save()

    ipv4_compute = IPAddress.objects.filter(virtance=virtance_old, network__type=Network.COMPUTE).first()
    wvcomp = WebVirtCompute(virtance_old.compute.token, virtance_old.compute.hostname)
    ipv4_compute_prefix = IPv4Network(f"{ipv4_float.address}/{ipv4_float.network.netmask}", strict=False).prefixlen
    res = wvcomp.float_ip_unassign(
        ipv4_compute.address, ipv4_float.address, ipv4_compute_prefix, ipv4_float.network.gateway
    )
    if isinstance(res, dict) and res.get("detail"):
        floatip_error(floatip.id, res.get("detail"), "reassign_floating_ip")
        virtance_error(virtance_old.id, res.get("detail"), "reassign_floating_ip")
    else:
        ipaddress.virtance = None
        ipaddress.save()

        floatip.event = FloatIP.ASSIGN
        floatip.save()

        virtance_old.reset_event()

        wvcomp = WebVirtCompute(virtance_new.compute.token, virtance_new.compute.hostname)
        ipv4_compute_prefix = IPv4Network(f"{ipv4_float.address}/{ipv4_float.network.netmask}", strict=False).prefixlen
        res = wvcomp.float_ip_assign(
            ipv4_compute.address, ipv4_float.address, ipv4_compute_prefix, ipv4_float.network.gateway
        )
        if isinstance(res, dict) and res.get("detail"):
            floatip_error(floatip.id, res.get("detail"), "reassign_floating_ip")
            virtance_error(virtance_new.id, res.get("detail"), "reassign_floating_ip")
        else:
            ipaddress.virtance = virtance_new
            ipaddress.save()

            virtance_new.reset_event()
            floatip.reset_event()


@app.task
def delete_floating_ip(floating_ip_id):
    error = False
    floatip = FloatIP.objects.get(id=floating_ip_id)
    virtance = floatip.ipaddress.virtance
    ipaddress = floatip.ipaddress
    floatip_counter = FloatIPCounter.objects.get(floatip=floatip)
    ipv4_float = IPAddress.objects.get(id=floatip.ipaddress.id)
    ipv4_compute = IPAddress.objects.filter(virtance=virtance, network__type=Network.COMPUTE).first()

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
            error = True
            floatip_error(floatip.id, res.get("detail"), "delete_floating_ip")
            virtance_error(virtance.id, res.get("detail"), "delete_floating_ip")
        else:
            virtance.reset_event()

    if error is False:
        floatip_counter.stop()
        floatip.delete()
        ipaddress.delete()


@app.task
def floating_ip_counter():
    new_period = False
    current_time = timezone.now()
    current_day = current_time.day
    current_hour = current_time.hour
    first_day_current_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if current_day == 1 and current_hour == 0:
        new_period = True

    for floatip in FloatIP.objects.filter(is_deleted=False):
        try:
            FloatIPCounter.objects.get(started__gt=first_day_current_month, stopped=None, floatip=floatip)
        except FloatIPCounter.DoesNotExist:
            period_start = current_time - timezone.timedelta(hours=1)
            if new_period is True:
                period_start = first_day_current_month
            FloatIPCounter.objects.create(
                floatip=floatip, ipaddress=floatip.ipaddress.address, amount=0.0, started=period_start
            )

    if new_period is True:
        prev_month = current_time - timezone.timedelta(days=1)
        last_day_prev_month = prev_month.replace(hour=23, minute=59, second=59, microsecond=999999)
        first_day_prev_month = prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        floating_ip_counters = FloatIPCounter.objects.filter(started__gt=first_day_prev_month, stopped=None)
        floating_ip_counters.update(stopped=last_day_prev_month)
    else:
        floating_ip_counters = FloatIPCounter.objects.filter(started__gt=first_day_current_month, stopped=None)
        for floatip_count in floating_ip_counters:
            floatip_count.amount += Decimal(0.0)
            floatip_count.save()
