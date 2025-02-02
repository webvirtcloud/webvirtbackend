import django_filters
from django.db.models import Q

from compute.models import Compute


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
