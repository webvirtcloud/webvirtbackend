import django_filters
from django.db.models import Q

from floating_ip.models import FloatIP


class FloatIPFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = FloatIP
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return FloatIP.objects.filter(
            Q(id__icontains=value) | Q(user__email__icontains=value) | Q(cidr__icontains=value), is_deleted=False
        )
