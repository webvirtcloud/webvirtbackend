from django.db.models import Sum
from django.conf import settings

from virtance.models import Virtance
from virtance.utils import virtance_error
from .models import Compute
from .webvirt import WebVirtCompute


CPU_USAGE_RATIO = settings.COMPUTE_CPU_RATIO_OVERCOMMIT
MEMORY_USAGE_RATIO = settings.COMPUTE_MEMORY_PERCENTAGE_USAGE / 100
STORAGE_USAGE_RATIO = settings.COMPUTE_STORAGE_PERCENTAGE_USAGE / 100


def assign_free_compute(virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)
    computes = Compute.objects.filter(
        region=virtance.region, is_active=True, is_deleted=False, arch=virtance.template.arch
    ).order_by("?")

    for compute in computes:
        cpu_used = (
            Virtance.objects.filter(compute=compute, is_deleted=False).aggregate(cpus=Sum("size__vcpu"))["cpus"] or 0
        )
        memory_used = (
            Virtance.objects.filter(compute=compute, is_deleted=False).aggregate(memory=Sum("size__memory"))["memory"]
            or 0
        )
        storage_used = (
            Virtance.objects.filter(compute=compute, is_deleted=False).aggregate(storage=Sum("size__disk"))["storage"]
            or 0
        )

        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_res = wvcomp.get_host_overview()
        storage_res = wvcomp.get_storage(settings.COMPUTE_VM_IMAGES_POOL)

        # Something checking for free resources :-)
        if host_res is not None and storage_res is not None:
            cpu_free = ((host_res["host"]["cpus"] * CPU_USAGE_RATIO) - cpu_used) > virtance.size.vcpu
            memory_free = ((host_res["host"]["memory"] * MEMORY_USAGE_RATIO) - memory_used) > virtance.size.memory
            storage_free = (
                (storage_res["storage"]["size"]["total"] * STORAGE_USAGE_RATIO) - storage_used
            ) > virtance.size.disk

            if cpu_free is True and memory_free is True and storage_free is True:
                virtance.compute = compute
                virtance.save()
                return compute.id

    virtance_error(virtance.id, "No compute found", event="assign_free_compute")
    return None
