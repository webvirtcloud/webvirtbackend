from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404

from floating_ip.models import FloatIP, FloatIPError
from admin.mixins import AdminTemplateView, AdminView


class AdminFloatIPIndexView(AdminTemplateView):
    template_name = "admin/floating_ip/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["floating_ips"] = FloatIP.objects.filter(is_deleted=False)
        return context


class AdminFloatIPDataView(AdminTemplateView):
    template_name = "admin/floating_ip/floating_ip.html"

    def get_object(self):
        return get_object_or_404(FloatIP, pk=self.kwargs["pk"], is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        floatip = self.get_object()
        context["floating_ip"] = floatip
        context["floating_ip_errors"] = FloatIPError.objects.filter(floatip=floatip)
        return context


class AdminFloatIPResetEventAction(AdminView):
    def get_object(self):
        return get_object_or_404(FloatIP, pk=self.kwargs["pk"], is_deleted=False)

    def post(self, request, *args, **kwargs):
        floatip = self.get_object()
        floatip.reset_event()
        return redirect(reverse("admin_floating_ip_data", args=[kwargs.get("pk")]))
