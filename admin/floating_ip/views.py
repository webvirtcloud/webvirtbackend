from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django_tables2 import SingleTableMixin, RequestConfig
from django_filters.views import FilterView

from .filters import FloatIPFilter
from .tables import FloatIPHTMxTable, FloatIPErrorTable
from floating_ip.models import FloatIP, FloatIPError
from admin.mixins import AdminTemplateView, AdminView


class AdminFloatIPIndexView(SingleTableMixin, FilterView, AdminView):
    table_class = FloatIPHTMxTable
    filterset_class = FloatIPFilter
    template_name = "admin/floating_ip/index.html"

    def get_queryset(self):
        return FloatIP.objects.filter(is_deleted=False)

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name


class AdminFloatIPDataView(AdminTemplateView):
    template_name = "admin/floating_ip/floating_ip.html"

    def get_object(self):
        return get_object_or_404(FloatIP, pk=self.kwargs["pk"], is_deleted=False)

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        floatip = self.get_object()

        floating_ip_errors = FloatIPError.objects.filter(floatip=floatip)
        floating_ip_errors_table = FloatIPErrorTable(floating_ip_errors)
        RequestConfig(self.request).configure(floating_ip_errors_table)

        context["floating_ip"] = floatip
        context["floating_ip_errors_table"] = floating_ip_errors_table
        return context


class AdminFloatIPResetEventAction(AdminView):
    def get_object(self):
        return get_object_or_404(FloatIP, pk=self.kwargs["pk"], is_deleted=False)

    def post(self, request, *args, **kwargs):
        floatip = self.get_object()
        floatip.reset_event()
        return redirect(reverse("admin_floating_ip_data", args=[kwargs.get("pk")]))
