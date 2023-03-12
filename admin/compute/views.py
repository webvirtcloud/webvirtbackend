from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from crispy_forms.helper import FormHelper
from .forms import FormCompute
from compute.models import Compute
from admin.mixins import AdminTemplateView, AdminFormView, AdminUpdateView, AdminDeleteView
from compute.helper import WebVirtCompute


class AdminComputeIndexView(AdminTemplateView):
    template_name = 'admin/compute/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['computes'] = Compute.objects.filter(is_deleted=False)
        return context


class AdminComputeCreateView(AdminFormView):
    template_name = 'admin/compute/create.html'
    form_class = FormCompute
    success_url = reverse_lazy('admin_compute_index')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class AdminComputeUpdateView(AdminUpdateView):
    template_name = 'admin/compute/update.html'
    template_name_suffix = "_form"
    model = Compute
    success_url = reverse_lazy('admin_compute_index')
    fields =  ["name", "arch", "description", "hostname", "token", "is_active"]

    def __init__(self, *args, **kwargs):
        super(AdminComputeUpdateView, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def get_context_data(self, **kwargs):
        context = super(AdminComputeUpdateView, self).get_context_data(**kwargs)
        context['helper'] = self.helper
        return context


class AdminComputeDeleteView(AdminDeleteView):
    template_name = 'admin/compute/delete.html'
    model = Compute
    success_url = reverse_lazy('admin_compute_index')

    def delete(self, request, *args, **kwargs):
        compute = self.get_object()
        compute.delete()
        return super(self).delete(request, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(AdminComputeDeleteView, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def get_context_data(self, **kwargs):
        context = super(AdminComputeDeleteView, self).get_context_data(**kwargs)
        context['helper'] = self.helper
        return context


class AdminComputeOverviewView(AdminTemplateView):
    template_name = 'admin/compute/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_overview = wvcomp.get_host_overview()
        context['compute'] = compute
        context['host_overview'] = host_overview
        return context


class AdminComputeStoragesView(AdminTemplateView):
    template_name = 'admin/compute/storages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_storages = wvcomp.get_host_storages()
        context['compute'] = compute
        context['storages'] = host_storages
        return context


class AdminComputeStoragePoolView(AdminTemplateView):
    template_name = 'admin/compute/storage_pool.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_storage_pool = wvcomp.get_host_storage_pool(kwargs.get("pool"))
        context['compute'] = compute
        context['storage_pool'] = host_storage_pool
        return context


class AdminComputeNetworksView(AdminTemplateView):
    template_name = 'admin/compute/networks.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_networks = wvcomp.get_host_networks()
        context['compute'] = compute
        context['networks'] = host_networks
        return context


class AdminComputeNetworkIfaceView(AdminTemplateView):
    template_name = 'admin/compute/network_iface.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_network_iface = wvcomp.get_host_network_iface(kwargs.get("iface"))
        context['compute'] = compute
        context['network_iface'] = host_network_iface
        return context


class AdminComputeSecretsView(AdminTemplateView):
    template_name = 'admin/compute/secrets.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_secrets = wvcomp.get_host_secrets()
        context['compute'] = compute
        context['secrets'] = host_secrets
        return context


class AdminComputeNwfiltersView(AdminTemplateView):
    template_name = 'admin/compute/nwfilters.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_nwfilters = wvcomp.get_host_nwfilters()
        print(host_nwfilters)
        context['compute'] = compute
        context['nwfilters'] = host_nwfilters
        return context
