import django_filters
from django.db.models import Q

from dbaas.models import DBaaS


class DBaaSFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = DBaaS
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return DBaaS.objects.filter(
            Q(id__icontains=value) | Q(user__email__icontains=value) | Q(name__icontains=value), is_deleted=False
        )
