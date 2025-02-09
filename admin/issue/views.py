from django.utils import timezone
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from image.models import ImageError
from firewall.models import FirewallError
from virtance.models import Virtance, VirtanceError
from floating_ip.models import FloatIPError
from admin.mixins import AdminView, AdminTemplateView
from .filters import IssueVirtanceFilter, IssueImageFilter, IssueFirewallFilter, IssueFloatIPFilter
from .tables import IssueVirtanceHTMxTable, IssueImageHTMxTable, IssueFirewallHTMxTable, IssueFloadIPHTMxTable


class AdminIssueIndexView(AdminTemplateView):
    template_name = "admin/issue/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AdminIssueVirtanceView(SingleTableMixin, FilterView, AdminView):
    table_class = IssueVirtanceHTMxTable
    filterset_class = IssueVirtanceFilter
    template_name = "admin/issue/virtance/index.html"

    def get_queryset(self):
        VirtanceError.objects.filter(
            virtance__type=Virtance.VIRTANCE,
            virtance__is_deleted=False,
            created__gte=timezone.now() - timezone.timedelta(days=30),
        )

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name


class AdminIssueImageView(SingleTableMixin, FilterView, AdminView):
    table_class = IssueImageHTMxTable
    filterset_class = IssueImageFilter
    template_name = "admin/issue/image/index.html"

    def get_queryset(self):
        return ImageError.objects.filter(
            image__is_deleted=False, created__gte=timezone.now() - timezone.timedelta(days=30)
        )

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name


class AdminIssueFirewallView(SingleTableMixin, FilterView, AdminView):
    table_class = IssueFirewallHTMxTable
    filterset_class = IssueFirewallFilter
    template_name = "admin/issue/firewall/index.html"

    def get_queryset(self, **kwargs):
        return FirewallError.objects.filter(
            firewall__is_deleted=False, created__gte=timezone.now() - timezone.timedelta(days=30)
        )

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name


class AdminIssueFloatIPView(SingleTableMixin, FilterView, AdminView):
    table_class = IssueFloadIPHTMxTable
    filterset_class = IssueFloatIPFilter
    template_name = "admin/issue/floatip/index.html"

    def get_queryset(self, **kwargs):
        return FloatIPError.objects.filter(
            floatip__is_deleted=False, created__gte=timezone.now() - timezone.timedelta(days=30)
        )

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name
