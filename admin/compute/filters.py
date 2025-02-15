import django_filters
from django.db.models import Q

from compute.models import Compute
from virtance.models import Virtance


class ComputeFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = Compute
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return Compute.objects.filter(
            Q(name__icontains=value)
            | Q(hostname__icontains=value)
            | Q(arch__icontains=value)
            | Q(region__name__icontains=value)
            | Q(description__icontains=value),
            is_deleted=False,
        )


class ComputeOverviewFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = Compute
        fields = ["query"]

    def __init__(self, *args, **kwargs):
        self.compute_id = kwargs.pop("compute_id", None)
        super().__init__(*args, **kwargs)

    def universal_search(self, queryset, name, value):
        return Virtance.objects.filter(
            Q(id__icontains=value)
            | Q(user__email__icontains=value)
            | Q(size__name__icontains=value)
            | Q(region__name__icontains=value),
            compute_id=self.compute_id,
            is_deleted=False,
        )
