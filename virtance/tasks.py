import time
from uuid import uuid4
from django.conf import settings
from django.utils import timezone
from passlib.hash import sha512_crypt

from webvirtcloud.celery import app
from compute.webvirt import WebVirtCompute
from compute.helper import (
    vm_name, 
    assign_free_compute
)
from network.helper import (
    assign_free_ipv4_public,
    assign_free_ipv4_compute,
    assign_free_ipv4_private,
)
from image.tasks import image_delete
from size.models import Size
from image.models import Image
from compute.models import Compute
from network.models import Network, IPAddress
from keypair.models import KeyPairVirtance
from .models import Virtance, VirtanceCounter
from .utils import virtance_error


def wvcomp_conn(compute):
    return WebVirtCompute(compute.token, compute.hostname)


@app.task
def create_virtance(virtance_id, password=None):
    keypairs = []
    compute = None
    ipv4_public = None
    ipv4_compute = None
    ipv4_private = None
    virtance = Virtance.objects.get(id=virtance_id)
    password = password if password else uuid4().hex[0:24]
    password_hash = sha512_crypt.encrypt(password, salt=uuid4().hex[0:8], rounds=5000)

    compute_id = assign_free_compute(virtance_id)
    if compute_id is not None:
        compute = Compute.objects.get(id=compute_id)
        
    ipv4_compute_id = assign_free_ipv4_compute(virtance_id)
    if ipv4_compute_id is not None:
        ipv4_compute = IPAddress.objects.get(id=ipv4_compute_id)

    ipv4_public_id = assign_free_ipv4_public(virtance_id)
    if ipv4_public_id is not None:
        ipv4_public = IPAddress.objects.get(id=ipv4_public_id)
    
    ipv4_private_id = assign_free_ipv4_private(virtance_id)
    if ipv4_private_id is not None:
        ipv4_private = IPAddress.objects.get(id=ipv4_private_id)

    for kpv in KeyPairVirtance.objects.filter(virtance_id=virtance_id):
        keypairs.append(kpv.keypair.public_key)

    if compute and ipv4_public and ipv4_compute and ipv4_private:
        images = [
            {
                "name": vm_name(virtance.id),
                "size": virtance.size.disk,
                "url": f"{settings.PUBLIC_IMAGES_URL}{virtance.template.file_name}",
                "md5sum": virtance.template.md5sum,
                "primary": True
            }
        ]
        network = {
            "v4": {
                "public": {
                    "primary": {
                        "address": ipv4_public.address,
                        "gateway": ipv4_public.network.gateway,
                        "netmask": ipv4_public.network.netmask,
                        "dns1": ipv4_public.network.dns1,
                        "dns2": ipv4_public.network.dns2
                        
                    },
                    "secondary": {
                        "address": ipv4_compute.address,
                        "gateway": ipv4_compute.network.gateway,
                        "netmask": ipv4_compute.network.netmask
                    }
                },
                "private": {
                    "address": ipv4_private.address,
                    "gateway": ipv4_private.network.gateway,
                    "netmask": ipv4_private.network.netmask
                }
            },
            "v6": None
        }

        virtance.compute = compute # TODO: race condition for database commit
        wvcomp = wvcomp_conn(compute)
        res = wvcomp.create_virtance(
            virtance.id,
            virtance.uuid.hex,
            virtance.name,
            virtance.size.vcpu,
            virtance.size.memory,
            images,
            network, 
            keypairs,
            password_hash,
        )
        if isinstance(res, dict) and res.get("detail"):
            virtance_error(virtance_id, res.get("detail"), "create")
        else:
            virtance.active()
            virtance.reset_event()
            VirtanceCounter.objects.create(
                virtance=virtance, size=virtance.size, amount=virtance.size.price, started=timezone.now()
            )


@app.task
def recreate_virtance(virtance_id):
    keypairs = []
    ipv4_public = None
    ipv4_compute = None
    ipv4_private = None
    virtance = Virtance.objects.get(id=virtance_id)
    compute = virtance.compute if virtance.compute else None
    password_hash = sha512_crypt.encrypt(uuid4().hex[0:24], salt=uuid4().hex[0:8], rounds=5000)

    if compute is None:
        compute_id = assign_free_compute(virtance_id)
        if compute_id is not None:
            compute = Compute.objects.get(id=compute_id)
            virtance.compute = compute

    try:
        ipv4_compute = IPAddress.objects.get(virtance=virtance, network__type=Network.COMPUTE)
    except IPAddress.DoesNotExist:
        ipv4_compute_id = assign_free_ipv4_compute(virtance_id)
        if ipv4_compute_id is not None:
            ipv4_compute = IPAddress.objects.get(id=ipv4_compute_id)
        
    try:
        ipv4_public = IPAddress.objects.get(virtance=virtance, network__type=Network.PUBLIC)
    except IPAddress.DoesNotExist:
        ipv4_public_id = assign_free_ipv4_public(virtance_id)
        if ipv4_public_id is not None:
            ipv4_public = IPAddress.objects.get(id=ipv4_public_id)
    
    try:
        ipv4_private = IPAddress.objects.get(virtance=virtance, network__type=Network.PRIVATE)
    except IPAddress.DoesNotExist:
        ipv4_private_id = assign_free_ipv4_private(virtance_id)
        if ipv4_private_id is not None:
            ipv4_private = IPAddress.objects.get(id=ipv4_private_id)

    for kpv in KeyPairVirtance.objects.filter(virtance_id=virtance_id):
        keypairs.append(kpv.keypair.public_key)

    if compute and ipv4_public and ipv4_compute and ipv4_private:
        images = [
            {
                "name": vm_name(virtance.id),
                "size": virtance.size.disk,
                "url": f"{settings.PUBLIC_IMAGES_URL}{virtance.template.file_name}",
                "md5sum": virtance.template.md5sum,
                "primary": True
            }
        ]
        network = {
            "v4": {
                "public": {
                    "primary": {
                        "address": ipv4_public.address,
                        "gateway": ipv4_public.network.gateway,
                        "netmask": ipv4_public.network.netmask,
                        "dns1": ipv4_public.network.dns1,
                        "dns2": ipv4_public.network.dns2
                        
                    },
                    "secondary": {
                        "address": ipv4_compute.address,
                        "gateway": ipv4_compute.network.gateway,
                        "netmask": ipv4_compute.network.netmask
                    }
                },
                "private": {
                    "address": ipv4_private.address,
                    "gateway": ipv4_private.network.gateway,
                    "netmask": ipv4_private.network.netmask
                }
            },
            "v6": None
        }

        wvcomp = wvcomp_conn(compute)
        res = wvcomp.create_virtance(
            virtance.id,
            virtance.uuid.hex,
            virtance.name,
            virtance.size.vcpu,
            virtance.size.memory,
            images,
            network, 
            keypairs,
            password_hash,
        )
        if isinstance(res, dict) and res.get("detail"):
            virtance_error(virtance_id, res.get("detail"), "create")
        else:
            virtance.active()
            virtance.reset_event()
            try:
                VirtanceCounter.objects.get(virtance=virtance, stopped=None)
            except VirtanceCounter.DoesNotExist:
                VirtanceCounter.objects.create(
                    virtance=virtance, size=virtance.size, amount=virtance.size.price, started=timezone.now()
                )


@app.task
def rebuild_virtance(virtance_id):
    keypairs = []
    ipv4_public = None
    ipv4_compute = None
    ipv4_private = None
    virtance = Virtance.objects.get(id=virtance_id)
    ipv4_public = IPAddress.objects.get(network__type=Network.PUBLIC, virtance=virtance)
    ipv4_compute = IPAddress.objects.get(network__type=Network.COMPUTE, virtance=virtance)
    ipv4_private = IPAddress.objects.get(network__type=Network.PRIVATE, virtance=virtance)
    password_hash = sha512_crypt.encrypt(uuid4().hex[0:24], salt=uuid4().hex[0:8], rounds=5000)

    for kpv in KeyPairVirtance.objects.filter(virtance=virtance):
        keypairs.append(kpv.keypair.public_key)
        
    images = [
        {
            "name": settings.VM_NAME_PREFIX + str(virtance.id),
            "size": virtance.size.disk,
            "url": f"{settings.PUBLIC_IMAGES_URL}{virtance.template.file_name}",
            "md5sum": virtance.template.md5sum,
            "primary": True
        }
    ]
    network = {
        "v4": {
            "public": {
                "primary": {
                    "address": ipv4_public.address,
                    "gateway": ipv4_public.network.gateway,
                    "netmask": ipv4_public.network.netmask,
                    "dns1": ipv4_public.network.dns1,
                    "dns2": ipv4_public.network.dns2
                    
                },
                "secondary": {
                    "address": ipv4_compute.address,
                    "gateway": ipv4_compute.network.gateway,
                    "netmask": ipv4_compute.network.netmask
                }
            },
            "private": {
                "address": ipv4_private.address,
                "gateway": ipv4_private.network.gateway,
                "netmask": ipv4_private.network.netmask
            }
        },
        "v6": None
    }
   
    wvcomp = wvcomp_conn(virtance.compute)
    res = wvcomp.rebuild_virtance(
        virtance.id, virtance.name, images, network, keypairs, password_hash
    )
    if res.get("detail") is None:
        virtance.active()
        virtance.reset_event()


@app.task
def action_virtance(virtance_id, action):
    error = None
    reboot = False
    if action == "reboot":
        reboot = True
        action = "shutdown"
    virtance = Virtance.objects.get(pk=virtance_id)
    wvcomp = wvcomp_conn(virtance.compute)
    res = wvcomp.action_virtance(virtance.id, action)
    error = res.get("detail")
    if error is None:
        if action == "shutdown":
            timeout = 60
            while wvcomp.status_virtance(virtance.id).get('status') != "shutoff":
                timeout -= 1
                time.sleep(1)
                if timeout == 0:
                    action = "power_off"
                    res = wvcomp.action_virtance(virtance.id, action)
                    error = res.get("detail")
                    if error is None:
                        virtance.inactive()
            else:
                virtance.inactive()
        if action == "power_on":
            virtance.active()
        if action == "power_off":
            virtance.inactive()
        if action == "power_cyrcle":
            virtance.active()
        if reboot is True:
            action = "power_on"
            res = wvcomp.action_virtance(virtance.id, action)
            error = res.get("detail")
            if error is None:
                virtance.active()
    if error is None:
        virtance.reset_event()     


@app.task
def resize_virtance(virtance_id, size_id):
    size = Size.objects.get(pk=size_id)
    virtance = Virtance.objects.get(pk=virtance_id)
    wvcomp = wvcomp_conn(virtance.compute)
    res = wvcomp.resize_virtance(virtance.id, size.vcpu, size.memory, size.disk)
    if res.get("detail") is None:
        virtance.active()
        virtance.reset_event()
        virtance.size = size
        virtance.save()
    else:
        virtance_error(virtance_id, res.get("detail"), "resize")


@app.task
def snapshot_virtance(virtance_id, display_name):
    virtance = Virtance.objects.get(pk=virtance_id)
    wvcomp = wvcomp_conn(virtance.compute)
    res = wvcomp.snapshot_virtance(virtance.id, uuid4().hex)
    if res.get("detail") is None:
        image = Image.objects.create(
            user=virtance.user,
            source=virtance,
            type=Image.SNAPSHOT,
            event=Image.CREATE,
            name=display_name,
            distribution=virtance.template.distribution,
            md5sum=res.get("md5sum"),
            file_name=res.get("file_name"),
            file_size=res.get("size"),
            disk_size=res.get("disk_size"),
            is_active=True
        )
        image.regions.add(virtance.region)
        image.reset_event()
        virtance.reset_event()
    else:
        virtance_error(virtance_id, res.get("detail"), "snapshot")


@app.task
def backup_virtance(virtance_id):
    file_name = uuid4().hex
    virtance = Virtance.objects.get(pk=virtance_id)
    wvcomp = wvcomp_conn(virtance.compute)
    res = wvcomp.snapshot_virtance(virtance.id, file_name)
    if res.get("detail") is None:
        image = Image.objects.create(
            user=virtance.user,
            source=virtance,
            type=Image.BACKUP,
            event=Image.CREATE,
            name=file_name,
            distribution=virtance.template.distribution,
            md5sum=res.get("md5sum"),
            file_name=res.get("file_name"),
            file_size=res.get("size"),
            disk_size=res.get("disk_size"),
            is_active=True
        )
        image.regions.add(virtance.region)
        image.reset_event()
        virtance.reset_event()
    else:
        virtance_error(virtance_id, res.get("detail"), "backup")


@app.task
def restore_virtance(virtance_id, image_name, disk_size):
    virtance = Virtance.objects.get(pk=virtance_id)
    wvcomp = wvcomp_conn(virtance.compute)
    res = wvcomp.restore_virtance(virtance_id, image_name, disk_size)
    if res.get("detail") is None:
        virtance.active()
        virtance.reset_event()
    else:
        virtance_error(virtance_id, res.get("detail"), "restore")


@app.task
def reset_password_virtance(virtance_id, password=None):
    if password is None:
        password = uuid4().hex[0:16]
    virtance = Virtance.objects.get(pk=virtance_id)
    wvcomp = wvcomp_conn(virtance.compute)
    password_hash = sha512_crypt.encrypt(password, salt=uuid4().hex[0:8], rounds=5000)
    res = wvcomp.reset_password_virtance(virtance.id, password_hash)
    if res.get("detail") is None:
        virtance.active()
        virtance.reset_event()
    else:
        virtance_error(virtance_id, res.get("detail"), "reset_password")


@app.task
def enable_recovery_mode_virtance(virtance_id):
    virtance = Virtance.objects.get(pk=virtance_id)
    wvcomp = wvcomp_conn(virtance.compute)
    res = wvcomp.get_virtance_media(virtance.id)
    if res.get("media"):
        if isinstance(res.get("media"), list):
            res = wvcomp.mount_virtance_media(virtance_id, res.get("media")[0].get("dev"), settings.RECOVERY_ISO_NAME)
            if res.get("detail") is None:
                virtance.active()
                virtance.enable_recovery_mode()
                virtance.reset_event()
    if res.get("detail"):
        virtance_error(virtance_id, res.get("detail"), "enable_recovery_mode")


@app.task
def disable_recovery_mode_virtance(virtance_id):
    reset_event = False
    virtance = Virtance.objects.get(pk=virtance_id)
    wvcomp = wvcomp_conn(virtance.compute)
    res = wvcomp.get_virtance_media(virtance.id)
    if res.get("media"):
        if isinstance(res.get("media"), list):
            if res.get("media")[0].get("path") is None:
                reset_event = True
            else:
                res = wvcomp.umount_virtance_media(
                    virtance_id, res.get("media")[0].get("dev"), res.get("media")[0].get("path")
                )
                if res.get("detail") is None:
                    reset_event = True

        if reset_event is True:
            virtance.active()
            virtance.disable_recovery_mode()
            virtance.reset_event()

    if res.get("detail"):
        virtance_error(virtance_id, res.get("detail"), "disable_recovery_mode")


@app.task
def delete_virtance(virtance_id):
    virtance = Virtance.objects.get(pk=virtance_id)
    wvcomp = wvcomp_conn(virtance.compute)
    res = wvcomp.delete_virtance(virtance.id)
    if res.get("detail") is None:
        ipaddresse = IPAddress.objects.filter(virtance=virtance)
        ipaddresse.delete()
        virtance.delete()

        current_time = timezone.now()
        first_day_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        try:
            virtance_counter = VirtanceCounter.objects.get(started__gt=first_day_month, virtance=virtance)
        except VirtanceCounter.DoesNotExist:
            virtance_counter = VirtanceCounter.objects.create(
                virtance=virtance, size=virtance.size, amount=virtance.size.price,
                started=current_time - timezone.timedelta(hours=1)
            )
        virtance_counter.stop()
    if res.get("detail"):
        virtance_error(virtance_id, res.get("detail"), "delete")


@app.task
def virtance_counter():
    current_time = timezone.now()
    current_day = current_time.day
    current_hour = current_time.hour
    first_day_current_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
   
    for virtance in Virtance.objects.filter(is_deleted=False):
        try:
            VirtanceCounter.objects.get(started__gt=first_day_current_month, virtance=virtance)
        except VirtanceCounter.DoesNotExist:
            period_start = current_time - timezone.timedelta(hours=1)
            VirtanceCounter.objects.create(
                virtance=virtance, size=virtance.size, amount=virtance.size.price,
                started=period_start
            )

    virtance_counters = VirtanceCounter.objects.filter(started__gt=first_day_current_month, stopped__isnull=True)

    if current_day == 1 and current_hour == 0:
        previous_month = current_time - timezone.timedelta(days=1)
        period_end = previous_month.replace(hour=23, minute=59, second=59, microsecond=0)
        virtance_counters.update(stopped=period_end)
    else:
        for virt_count in virtance_counters:
            virt_count.amount += virt_count.size.price
            virt_count.save()


@app.task
def virtance_backup():
    compute_event_backup_ids = []

    compute_ids = Virtance.objects.filter(
        is_backup_enabled=True, 
        event=Virtance.BACKUP, 
        is_deleted=False
    ).values_list('compute_id', flat=True)

    virtances = Virtance.objects.filter(
        is_backup_enabled=True,
        event=None,
        is_deleted=False
    ).exclude(compute__in=list(set(compute_ids)))

    for virtance in virtances:
        backups = Image.objects.filter(virtance=virtance, type=Image.BACKUP, is_deleted=False)

        if virtance.compute.id not in compute_event_backup_ids:
            compute_event_backup_ids.append(virtance.compute.id)

            if backups:
                if (timezone.now() - backups.first().created).days >= settings.BACKUP_PERIOD_DAYS:
                    backup_virtance.delay(virtance.id)
                    virtance.event = Virtance.BACKUP
                    virtance.save()
                if len(backups) > settings.BACKUP_PER_MONTH:
                    image_delete.delay(backups.last().id)
            else:
                backup_virtance.delay(virtance.id)
                virtance.event = Virtance.BACKUP
                virtance.save()
