from django.conf import settings

from virtance.models import Virtance
from virtance.utils import virtance_error
from .models import Compute


def vm_name(virtance_id):
    return f"{settings.VM_NAME_PREFIX}{str(virtance_id)}"


def assign_free_compute(virtance_id):
    virtance = Virtance.objects.get(id=virtance_id)
    computes = Compute.objects.filter(
        region=virtance.region, is_active=True, is_deleted=False, arch=virtance.template.arch
    ).order_by("?")

    for compute in computes:  # TODO: check if compute is available
        virtance.compute = compute
        virtance.save()
        return compute.id

    virtance_error(virtance.id, "No compute found", event="assign_free_compute")
    return None
