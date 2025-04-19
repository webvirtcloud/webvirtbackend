from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from admin.mixins import AdminTemplateView, AdminView
from dbaas.models import DBaaS
from dbaas.tasks import create_dbaas
from network.models import IPAddress, Network
from virtance.utils import decrypt_data, encrypt_data, make_passwd, make_ssh_private

from .filters import DBaaSFilter
from .tables import DBaaSHTMxTable


class AdminDBaaSIndexView(SingleTableMixin, FilterView, AdminView):
    table_class = DBaaSHTMxTable
    filterset_class = DBaaSFilter
    template_name = "admin/dbaas/index.html"

    def get_queryset(self):
        return DBaaS.objects.filter(is_deleted=False)

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name


class AdminDBaaSDataView(AdminTemplateView):
    template_name = "admin/dbaas/dbaas.html"

    def get_object(self):
        return get_object_or_404(DBaaS, pk=self.kwargs["pk"], is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dbaas = self.get_object()
        context["dbaas"] = dbaas
        context["ipv4_public"] = IPAddress.objects.get(network__type=Network.PUBLIC, virtance=dbaas.virtance)
        context["ipv4_private"] = IPAddress.objects.get(network__type=Network.PRIVATE, virtance=dbaas.virtance)
        context["ipv4_compute"] = IPAddress.objects.get(network__type=Network.COMPUTE, virtance=dbaas.virtance)
        return context


class AdminDBaaSRecreateAction(AdminView):
    def get_object(self):
        return get_object_or_404(DBaaS, pk=self.kwargs["pk"], is_deleted=False)

    def post(self, request, *args, **kwargs):
        dbaas = self.get_object()
        virtance = dbaas.virtance
        virtance.event = virtance.CREATE
        virtance.save()
        dbaas.event = DBaaS.CREATE
        dbaas.private_key = encrypt_data(make_ssh_private())
        dbaas.admin_secret = encrypt_data(make_passwd(length=16))
        dbaas.master_secret = encrypt_data(make_passwd(length=16))
        dbaas.save()
        create_dbaas.delay(dbaas.id)
        return redirect(reverse("admin_dbaas_data", args=[kwargs.get("pk")]))


class AdminDBaaSDownlodPrivateKeyAction(AdminView):
    def get_object(self):
        return get_object_or_404(DBaaS, pk=self.kwargs["pk"], is_deleted=False)

    def get(self, request, *args, **kwargs):
        dbaas = self.get_object()
        private_key = decrypt_data(dbaas.private_key)
        return HttpResponse(
            private_key,
            content_type="application/text",
            charset="utf-8",
            headers={"Content-Disposition": "attachment; filename=private.pem"},
        )


class AdminDBaaSResetEventAction(AdminView):
    def get_object(self):
        return get_object_or_404(DBaaS, pk=self.kwargs["pk"], is_deleted=False)

    def post(self, request, *args, **kwargs):
        dbaas = self.get_object()
        dbaas.reset_event()
        return redirect(reverse("admin_dbaas_data", args=[kwargs.get("pk")]))
