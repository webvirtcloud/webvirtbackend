import django_filters
from django.db.models import Q

from network.models import Network


class NetworkFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = Network
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return Network.objects.filter(
            Q(cidr__icontains=value)
            | Q(netmask__icontains=value)
            | Q(region__name__icontains=value)
            | Q(type__icontains=value)
            | Q(version__icontains=value),
            is_deleted=False,
        )
