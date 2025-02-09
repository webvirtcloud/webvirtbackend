import django_filters
from django.db.models import Q
from django.utils import timezone

from image.models import ImageError
from firewall.models import FirewallError
from virtance.models import Virtance, VirtanceError
from floating_ip.models import FloatIPError


class IssueVirtanceFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = VirtanceError
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return VirtanceError.objects.filter(
            Q(virtance__id__iconaince=value) | Q(event__icontains=value) | Q(message__icontains=value),
            virtacne__type=Virtance.VIRTANCE,
            virtance__is_deleted=False,
            created__gte=timezone.now() - timezone.timedelta(days=30),
        )


class IssueImageFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = ImageError
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return ImageError.objects.filter(
            Q(image__id__iconaince=value) | Q(event__icontains=value) | Q(message__icontains=value),
            image__is_deleted=False,
            created__gte=timezone.now() - timezone.timedelta(days=30),
        )


class IssueFirewallFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = FirewallError
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return FirewallError.objects.filter(
            Q(firewall__id__iconaince=value) | Q(event__icontains=value) | Q(message__icontains=value),
            firewall__is_deleted=False,
            created__gte=timezone.now() - timezone.timedelta(days=30),
        )


class IssueFloatIPFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method="universal_search", label="")

    class Meta:
        model = FloatIPError
        fields = ["query"]

    def universal_search(self, queryset, name, value):
        return FloatIPError.objects.filter(
            Q(floatip__id__iconaince=value) | Q(event__icontains=value) | Q(message__icontains=value),
            floatip__is_deleted=False,
            created__gte=timezone.now() - timezone.timedelta(days=30),
        )
