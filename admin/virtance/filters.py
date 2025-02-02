import django_filters
from django.db.models import Q

from virtance.models import Virtance


class VirtanceFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = Virtance
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return Virtance.objects.filter(
            Q(id__icontains=value)
            | Q(user__email__icontains=value)
            | Q(type__icontains=value)
            | Q(region__name__icontains=value)
            | Q(size__name__icontains=value)
            | Q(compute__name__icontains=value),
            is_deleted=False,
        )
