from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from .filters import FirewallFilter
from .tables import FirewallHTMxTable
from admin.mixins import AdminView, AdminTemplateView
from firewall.models import Firewall, Rule, FirewallVirtance, FirewallError


class AdminFirewallIndexView(SingleTableMixin, FilterView, AdminView):
    table_class = FirewallHTMxTable
    filterset_class = FirewallFilter
    template_name = "admin/firewall/index.html"

    def get_queryset(self):
        firewalls = Firewall.objects.filter(is_deleted=False)
        for firewall in firewalls:
            firewall.num_rule = Rule.objects.filter(firewall=firewall).count()
            firewall.num_virtance = FirewallVirtance.objects.filter(firewall=firewall).count()
        return firewalls

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
        context["firewall"] = firewall
        context["rules"] = Rule.objects.filter(firewall=firewall)
        context["virtances"] = FirewallVirtance.objects.filter(firewall=firewall)
        context["firewall_errors"] = FirewallError.objects.filter(firewall=firewall)
        return context


class AdminFirewallResetEventAction(AdminView):
    def get_object(self):
        return get_object_or_404(Firewall, pk=self.kwargs["pk"], is_deleted=False)

    def post(self, request, *args, **kwargs):
        firewall = self.get_object()
        firewall.reset_event()
        return redirect(reverse("admin_firewall_data", args=[kwargs.get("pk")]))
