import django_filters
from django.db.models import Q

from lbaas.models import LBaaS


class LBaaSFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = LBaaS
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return LBaaS.objects.filter(
            Q(id__icontains=value) | Q(user__email__icontains=value) | Q(name__icontains=value), is_deleted=False
        )
