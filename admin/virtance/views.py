from django.shortcuts import get_object_or_404

from virtance.models import Virtance
from network.models import IPAddress, Network
from admin.mixins import AdminTemplateView


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
        ipv4public = IPAddress.objects.filter(virtance=virtance, network__type=Network.PUBLIC).first()
        ipv4private = IPAddress.objects.filter(virtance=virtance, network__type=Network.PRIVATE).first()
        ipv4compute = IPAddress.objects.filter(virtance=virtance, network__type=Network.COMPUTE).first()
        context['virtance'] = virtance
        context['ipv4public'] = ipv4public
        context['ipv4private'] = ipv4private
        context['ipv4compute'] = ipv4compute
        return context
