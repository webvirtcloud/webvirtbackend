from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404

from admin.mixins import AdminView, AdminTemplateView
from lbaas.models import LBaaS, LBaaSForwadRule, LBaaSVirtance


class AdminLBaaSIndexView(AdminTemplateView):
    template_name = "admin/lbaas/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lbaas = LBaaS.objects.filter(is_deleted=False)
        for lb in lbaas:
            lb.num_rule = len(LBaaSForwadRule.objects.filter(lbaas=lbaas, is_deleted=False))
            lb.num_virtance = len(LBaaSVirtance.objects.filter(lbaas=lbaas, is_deleted=False))
        context["lbaas"] = lbaas
        return context


class AdminLBaaSDataView(AdminTemplateView):
    template_name = "admin/lbaas/lbaas.html"

    def get_object(self):
        return get_object_or_404(LBaaS, pk=self.kwargs["pk"], is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lbaas = self.get_object()
        context["lbaas"] = lbaas
        context["rules"] = LBaaSForwadRule.objects.filter(lbaas=lbaas, is_deleted=False)
        context["virtances"] = LBaaSVirtance.objects.filter(lbaas=lbaas, is_deleted=False)
        return context


class AdminLBaaSResetEventAction(AdminView):
    def get_object(self):
        return get_object_or_404(LBaaS, pk=self.kwargs["pk"], is_deleted=False)

    def post(self, request, *args, **kwargs):
        lbaas = self.get_object()
        lbaas.reset_event()
        return redirect(reverse("admin_lbaas_data", args=[kwargs.get("pk")]))
