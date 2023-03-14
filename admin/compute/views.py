from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from crispy_forms.helper import FormHelper
from .forms import FormCompute, FormStartAction, FormAutostartAction
from .forms import FormVolumeCloneAction, FormVolumeResizeAction
from compute.models import Compute
from admin.mixins import AdminView, AdminTemplateView, AdminFormView, AdminUpdateView, AdminDeleteView
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
        host_storages = wvcomp.get_storages()
        context['compute'] = compute
        context['storages'] = host_storages
        return context


class AdminComputeStorageView(AdminTemplateView):
    template_name = 'admin/compute/storage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_storage_pool = wvcomp.get_storage(kwargs.get("pool"))
        context['compute'] = compute
        context['form_start'] = FormStartAction()
        context['form_autostart'] = FormAutostartAction()
        context['storage_pool'] = host_storage_pool
        return context

    def post(self, request, *args, **kwargs):
        form_start = FormStartAction(request.POST)
        form_autostart = FormAutostartAction(request.POST)
        context = self.get_context_data(*args, **kwargs)

        if form_start.is_valid():
            compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
            wvcomp = WebVirtCompute(compute.token, compute.hostname)
            res = wvcomp.set_storage_action(kwargs.get("pool"), form_start.cleaned_data.get("action"))
            if res.get("detail") is None:
                return redirect(self.request.get_full_path())
            else:
                form_start.add_error("__all__", res.get("detail"))
                context['form_start'] = form_start

        if form_autostart.is_valid():
            compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
            wvcomp = WebVirtCompute(compute.token, compute.hostname)
            res = wvcomp.set_storage_action(kwargs.get("pool"), form_autostart.cleaned_data.get("action"))
            if res.get("detail") is None:
                return redirect(self.request.get_full_path())
            else:
                form_autostart.add_error("__all__", res.get("detail"))
                context['form_autostart'] = form_autostart
            
        return self.render_to_response(context)


class AdminComputeStorageVolumeDeleteView(AdminView):

    def get(self, request, *args, **kwargs):
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.delete_storage_volume(kwargs.get("pool"), kwargs.get("vol"))
        if res.get("detail") is None:
            messages.success(request, "Volume successfuly deleted.")
        else:
            messages.errors(request, res.get("detail"))
        return redirect(reverse('admin_compute_storage', args=[kwargs.get("pk"), kwargs.get("pool")]))


class AdminComputeStorageVolumeDeleteView(AdminFormView):

    def get(self, request, *args, **kwargs):
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.delete_storage_volume(kwargs.get("pool"), kwargs.get("vol"))
        if res.get("detail") is None:
            messages.success(request, "Volume successfuly deleted.")
        else:
            messages.error(request, res.get("detail"))
        return redirect(reverse('admin_compute_storage', args=[kwargs.get("pk"), kwargs.get("pool")]))


class AdminComputeStorageVolumeCloneView(AdminFormView):
    template_name = 'admin/compute/volume_clone.html'
    form_class = FormVolumeCloneAction
    success_url = reverse_lazy('admin_compute_storage')

    def form_valid(self, form):
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.action_storage_volume(
            self.kwargs.get("pool"), self.kwargs.get("vol"), "clone", form.cleaned_data.get("name")
        )
        if res.get("detail") is not None:
            form.add_error("__all__", res.get("detail"))
            return super().form_invalid(form)
            
        self.success_url = reverse('admin_compute_storage', args=[self.kwargs.get("pk"), self.kwargs.get("pool")])
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        context["compute"] = compute
        context["pool"] = self.kwargs.get("pool")
        context["vol"] = self.kwargs.get("vol")
        return context


class AdminComputeStorageVolumeResizeView(AdminFormView):
    template_name = 'admin/compute/volume_resize.html'
    form_class = FormVolumeResizeAction

    def form_valid(self, form):
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.action_storage_volume(
            self.kwargs.get("pool"), self.kwargs.get("vol"), "resize", form.cleaned_data.get("size") * (1024**3)
        )
        if res.get("detail") is not None:
            form.add_error("__all__", res.get("detail"))
            return super().form_invalid(form)
            
        self.success_url = reverse('admin_compute_storage', args=[self.kwargs.get("pk"), self.kwargs.get("pool")])
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        context["compute"] = compute
        context["pool"] = self.kwargs.get("pool")
        context["vol"] = self.kwargs.get("vol")
        return context


class AdminComputeNetworksView(AdminTemplateView):
    template_name = 'admin/compute/networks.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_networks = wvcomp.get_networks()
        context['compute'] = compute
        context['networks'] = host_networks
        return context


class AdminComputeNetworkView(AdminTemplateView):
    template_name = 'admin/compute/network.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_network_pool = wvcomp.get_network(kwargs.get("pool"))
        context['compute'] = compute
        context['form_start'] = FormStartAction()
        context['form_autostart'] = FormAutostartAction()
        context['network_pool'] = host_network_pool
        return context

    def post(self, request, *args, **kwargs):
        form_start = FormStartAction(request.POST)
        form_autostart = FormAutostartAction(request.POST)
        context = self.get_context_data(*args, **kwargs)

        if form_start.is_valid():
            compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
            wvcomp = WebVirtCompute(compute.token, compute.hostname)
            res = wvcomp.set_storage_action(kwargs.get("pool"), form_start.cleaned_data.get("action"))
            if res.get("detail") is None:
                return redirect(self.request.get_full_path())
            else:
                form_start.add_error("__all__", res.get("detail"))
                context['form_start'] = form_start

        if form_autostart.is_valid():
            compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
            wvcomp = WebVirtCompute(compute.token, compute.hostname)
            res = wvcomp.set_storage_action(kwargs.get("pool"), form_autostart.cleaned_data.get("action"))
            if res.get("detail") is None:
                return redirect(self.request.get_full_path())
            else:
                form_autostart.add_error("__all__", res.get("detail"))
                context['form_autostart'] = form_autostart
            
        return self.render_to_response(context)


class AdminComputeSecretsView(AdminTemplateView):
    template_name = 'admin/compute/secrets.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_secrets = wvcomp.get_secrets()
        context['compute'] = compute
        context['secrets'] = host_secrets
        return context


class AdminComputeNwfiltersView(AdminTemplateView):
    template_name = 'admin/compute/nwfilters.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        host_nwfilters = wvcomp.get_nwfilters()
        context['compute'] = compute
        context['nwfilters'] = host_nwfilters
        return context
