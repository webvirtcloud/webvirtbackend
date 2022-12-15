from virtance.models import Virtance
from .models import Compute


def assign_free_compute(virtance_id):
    virtance = virtance.objects.get(id=virtance_id)
    computes = Compute.objects.filter(
        region=virtance.region, is_active=True, is_deleted=False
    ).order_by("?")
    for compute in computes: # TODO: check if compute is available
        virtance.compute = compute
        virtance.save()
    return False
