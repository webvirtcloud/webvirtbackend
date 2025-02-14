from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, RequestConfig

from .filters import FirewallFilter
from .tables import FirewallHTMxTable, FirewallRuleTable, FirewallVirtanceTable, FirewallErrorTable
from admin.mixins import AdminView, AdminTemplateView
from firewall.models import Firewall, Rule, FirewallVirtance, FirewallError


class AdminFirewallIndexView(SingleTableMixin, FilterView, AdminView):
    table_class = FirewallHTMxTable
    filterset_class = FirewallFilter
    template_name = "admin/firewall/index.html"

    def get_queryset(self):
        return Firewall.objects.filter(is_deleted=False)

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name


class AdminFirewallDataView(AdminTemplateView):
    template_name = "admin/firewall/firewall.html"

    def get_object(self):
        return get_object_or_404(Firewall, pk=self.kwargs["pk"], is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        firewall = self.get_object()

        rules = Rule.objects.filter(firewall=firewall)
        firewall_rules_table = FirewallRuleTable(rules)
        RequestConfig(self.request).configure(firewall_rules_table)

        virtances = FirewallVirtance.objects.filter(firewall=firewall)
        firewall_virtances_table = FirewallVirtanceTable(virtances)
        RequestConfig(self.request).configure(firewall_virtances_table)

        firewall_errors = FirewallError.objects.filter(firewall=firewall)
        firewall_errors_table = FirewallErrorTable(firewall_errors)
        RequestConfig(self.request).configure(firewall_errors_table)

        context["firewall"] = firewall
        context["firewall_rules_table"] = firewall_rules_table
        context["firewall_errors_table"] = firewall_errors_table
        context["firewall_virtances_table"] = firewall_virtances_table
        return context


class AdminFirewallResetEventAction(AdminView):
    def get_object(self):
        return get_object_or_404(Firewall, pk=self.kwargs["pk"], is_deleted=False)

    def post(self, request, *args, **kwargs):
        firewall = self.get_object()
        firewall.reset_event()
        return redirect(reverse("admin_firewall_data", args=[kwargs.get("pk")]))
