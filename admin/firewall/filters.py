import django_filters
from django.db.models import Q

from firewall.models import Firewall


class FirewallFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = Firewall
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return Firewall.objects.filter(
            Q(id__icontains=value) | Q(user__email__icontains=value) | Q(name__icontains=value), is_deleted=False
        )
