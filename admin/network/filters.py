import django_filters
from django.db.models import Q

from network.models import IPAddress, Network


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


class NetworkListFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = IPAddress
        fields = ["query"]

    def __init__(self, *args, **kwargs):
        self.network_id = kwargs.pop("network_id", None)
        super().__init__(*args, **kwargs)

    def universal_search(self, queryset, name, value):
        return IPAddress.objects.filter(
            Q(address__icontains=value) | Q(virtance__id__icontains=value),
            network_id=self.network_id,
        )
