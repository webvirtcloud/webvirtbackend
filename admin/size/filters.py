import django_filters
from django.db.models import Q

from size.models import Size


class SizeFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = Size
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return Size.objects.filter(
            Q(slug__icontains=value) | Q(name__icontains=value) | Q(description__icontains=value), is_deleted=False
        )
