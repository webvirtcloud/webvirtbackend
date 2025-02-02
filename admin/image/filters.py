import django_filters
from django.db.models import Q

from image.models import Image


class ImageFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = Image
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return Image.objects.filter(
            (Q(type=Image.BACKUP) | Q(type=Image.SNAPSHOT)),
            Q(id__icontains=value) | Q(user__email__icontains=value) | Q(type__icontains=value),
            is_deleted=False,
        )
