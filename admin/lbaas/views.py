from django.urls import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, RequestConfig

from .filters import LBaaSFilter
from .tables import LBaaSHTMxTable, HealthTable, RulesTable, VirtancesTable
from admin.mixins import AdminView, AdminTemplateView
from network.models import IPAddress, Network
from lbaas.models import LBaaS, LBaaSForwadRule, LBaaSVirtance
from lbaas.tasks import create_lbaas, reload_lbaas
from virtance.utils import make_ssh_private, decrypt_data, encrypt_data


class AdminLBaaSIndexView(SingleTableMixin, FilterView, AdminView):
    table_class = LBaaSHTMxTable
    filterset_class = LBaaSFilter
    template_name = "admin/lbaas/index.html"

    def get_queryset(self):
        return LBaaS.objects.filter(is_deleted=False)

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name


class AdminLBaaSDataView(AdminTemplateView):
    template_name = "admin/lbaas/lbaas.html"

    def get_object(self):
        return get_object_or_404(LBaaS, pk=self.kwargs["pk"], is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lbaas = self.get_object()

        health = [
            {
                "protocol": lbaas.check_protocol,
                "port": lbaas.check_port,
                "path": lbaas.check_path,
                "interval": lbaas.check_interval_seconds,
                "timeout": lbaas.check_timeout_seconds,
                "healthy": lbaas.check_healthy_threshold,
                "unhealthy": lbaas.check_unhealthy_threshold,
            },
        ]
        health_table = HealthTable(health)
        RequestConfig(self.request).configure(health_table)

        rules = LBaaSForwadRule.objects.filter(lbaas=lbaas, is_deleted=False)
        rules_table = RulesTable(rules)
        RequestConfig(self.request).configure(rules_table)

        virtances = LBaaSVirtance.objects.filter(lbaas=lbaas, is_deleted=False)
        virtances_table = VirtancesTable(virtances)
        RequestConfig(self.request).configure(virtances_table)

        context["lbaas"] = lbaas
        context["rules_table"] = rules_table
        context["health_table"] = health_table
        context["virtances_table"] = virtances_table
        context["ipv4_public"] = IPAddress.objects.get(network__type=Network.PUBLIC, virtance=lbaas.virtance)
        context["ipv4_private"] = IPAddress.objects.get(network__type=Network.PRIVATE, virtance=lbaas.virtance)
        context["ipv4_compute"] = IPAddress.objects.get(network__type=Network.COMPUTE, virtance=lbaas.virtance)
        return context


class AdminLBaaSRecreateAction(AdminView):
    def get_object(self):
        return get_object_or_404(LBaaS, pk=self.kwargs["pk"], is_deleted=False)

    def post(self, request, *args, **kwargs):
        lbaas = self.get_object()
        virtance = lbaas.virtance
        virtance.event = virtance.CREATE
        virtance.save()
        lbaas.event = LBaaS.CREATE
        lbaas.private_key = encrypt_data(make_ssh_private())
        lbaas.save()
        create_lbaas.delay(lbaas.id)
        return redirect(reverse("admin_lbaas_data", args=[kwargs.get("pk")]))


class AdminLBaaSReloadAction(AdminView):
    def get_object(self):
        return get_object_or_404(LBaaS, pk=self.kwargs["pk"], is_deleted=False)

    def post(self, request, *args, **kwargs):
        lbaas = self.get_object()
        lbaas.event = LBaaS.RELOAD
        lbaas.save()
        reload_lbaas.delay(lbaas.id)
        return redirect(reverse("admin_lbaas_data", args=[kwargs.get("pk")]))


class AdminLBaaSDownlodPrivateKeyAction(AdminView):
    def get_object(self):
        return get_object_or_404(LBaaS, pk=self.kwargs["pk"], is_deleted=False)

    def get(self, request, *args, **kwargs):
        lbaas = self.get_object()
        private_key = decrypt_data(lbaas.private_key)
        return HttpResponse(
            private_key,
            content_type="application/text",
            charset="utf-8",
            headers={"Content-Disposition": f"attachment; filename=private.pem"},
        )


class AdminLBaaSResetEventAction(AdminView):
    def get_object(self):
        return get_object_or_404(LBaaS, pk=self.kwargs["pk"], is_deleted=False)

    def post(self, request, *args, **kwargs):
        lbaas = self.get_object()
        lbaas.reset_event()
        return redirect(reverse("admin_lbaas_data", args=[kwargs.get("pk")]))
