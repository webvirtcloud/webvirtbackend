from django.conf import settings
from django.shortcuts import get_object_or_404

from network.models import IPAddress, Network
from virtance.models import Virtance, VirtanceError
from admin.mixins import AdminTemplateView
from compute.helper import WebVirtCompute


class AdminVirtanceIndexView(AdminTemplateView):
    template_name = 'admin/virtance/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['virtances'] = Virtance.objects.filter(is_deleted=False)
        return context


class AdminVirtanceDataView(AdminTemplateView):
    template_name = 'admin/virtance/virtance.html'

    def get_object(self):
        return get_object_or_404(Virtance, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        virtance = self.get_object()
        virtance_errors = VirtanceError.objects.filter(virtance=virtance)
        ipv4public = IPAddress.objects.filter(virtance=virtance, network__type=Network.PUBLIC).first()
        ipv4private = IPAddress.objects.filter(virtance=virtance, network__type=Network.PRIVATE).first()
        ipv4compute = IPAddress.objects.filter(virtance=virtance, network__type=Network.COMPUTE).first()
        context['virtance'] = virtance
        context['ipv4public'] = ipv4public
        context['ipv4private'] = ipv4private
        context['ipv4compute'] = ipv4compute
        context['virtance_errors'] = virtance_errors
        return context


class AdminVirtanceConsoleView(AdminTemplateView):
    template_name = 'admin/virtance/console.html'

    def get_object(self):
        return get_object_or_404(Virtance, pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        virtance = self.get_object()
        response = super(AdminVirtanceConsoleView, self).get(request, *args, **kwargs)
        response.set_cookie(
            "uuid",
            virtance.uuid,
            httponly=True,
            domain=settings.SESSION_COOKIE_DOMAIN
        )
        return response


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        virtance = self.get_object()
        wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
        res = wvcomp.get_virtance_vnc(virtance.id)
        vnc_password = res.get("vnc_password")
        console_host = settings.NOVNC_URL
        console_port = settings.NOVNC_PORT
        context['virtance'] = virtance
        context['vnc_password'] = vnc_password
        context['console_host'] = console_host
        context['console_port'] = console_port
        return context
