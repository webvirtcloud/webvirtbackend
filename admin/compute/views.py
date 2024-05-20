from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from crispy_forms.helper import FormHelper
from .forms import FormNetworkCreate, FormStorageDirCreate, FormStorageRBDCreate
from .forms import FormCompute, FormStartAction, FormAutostartAction
from .forms import FormSecretCreateAction, FormSecretValueAction, FormNwfilterCreateAction
from .forms import FormVolumeCreateAction, FormVolumeCloneAction, FormVolumeResizeAction
from compute.models import Compute
from virtance.models import Virtance
from network.models import Network
from admin.mixins import AdminView, AdminTemplateView, AdminFormView, AdminUpdateView, AdminDeleteView
from compute.webvirt import WebVirtCompute


class AdminComputeIndexView(AdminTemplateView):
    template_name = "admin/compute/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["computes"] = Compute.objects.filter(is_deleted=False)
        return context


class AdminComputeCreateView(AdminFormView):
    template_name = "admin/compute/create.html"
    form_class = FormCompute
    success_url = reverse_lazy("admin_compute_index")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class AdminComputeUpdateView(AdminUpdateView):
    template_name = "admin/compute/update.html"
    template_name_suffix = "_form"
    model = Compute
    success_url = reverse_lazy("admin_compute_index")
    fields = ["name", "arch", "description", "hostname", "token", "is_active"]

    def __init__(self, *args, **kwargs):
        super(AdminComputeUpdateView, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def form_valid(self, form):
        if form.has_changed():
            if form.cleaned_data.get("is_active") is True:
                compute = self.get_object()
                network = Network.objects.filter(region=compute.region, is_deleted=False)
                if not network.filter(type=Network.COMPUTE).exists():
                    form.add_error("__all__", "There is no COMPUTE network in the region.")
                    return super().form_invalid(form)
                if not network.filter(type=Network.PRIVATE).exists():
                    form.add_error("__all__", "There is no PRIVATE network in the region.")
                    return super().form_invalid(form)
                if not network.filter(type=Network.PUBLIC).exists():
                    form.add_error("__all__", "There is no PUBLIC network in the region.")
                    return super().form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(AdminComputeUpdateView, self).get_context_data(**kwargs)
        context["helper"] = self.helper
        return context


class AdminComputeDeleteView(AdminDeleteView):
    template_name = "admin/compute/delete.html"
    model = Compute
    success_url = reverse_lazy("admin_compute_index")

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
        context["helper"] = self.helper
        return context


class AdminComputeOverviewView(AdminTemplateView):
    template_name = "admin/compute/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        virtances = Virtance.objects.filter(compute=compute, is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.get_host_overview()
        messages.error(self.request, res.get("detail"))
        context["compute"] = compute
        context["virtances"] = virtances
        context["host_overview"] = res
        return context


class AdminComputeStoragesView(AdminTemplateView):
    template_name = "admin/compute/storages.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.get_storages()
        messages.error(self.request, res.get("detail"))
        context["compute"] = compute
        context["storages"] = res.get("storages")
        return context


class AdminComputeStorageDirCreateView(AdminFormView):
    template_name = "admin/compute/storage_dir_create.html"
    form_class = FormStorageDirCreate

    def form_valid(self, form):
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.create_storage_dir(form.cleaned_data.get("name"), form.cleaned_data.get("target"))
        if res.get("detail") is None:
            return super().form_valid(form)
        form.add_error("__all__", res.get("detail"))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        context["compute"] = compute
        return context

    def get_success_url(self):
        return reverse("admin_compute_storages", args=[self.kwargs.get("pk")])


class AdminComputeStorageRBDCreateView(AdminFormView):
    template_name = "admin/compute/storage_rbd_create.html"
    form_class = FormStorageRBDCreate

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.get_secrets()
        form.fields["secret"].choices = [(secret.get("uuid"), secret.get("uuid")) for secret in res.get("secrets")]
        return form

    def form_valid(self, form):
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.create_storage_rbd(
            form.cleaned_data.get("name"),
            form.cleaned_data.get("pool"),
            form.cleaned_data.get("user"),
            form.cleaned_data.get("secret"),
            form.cleaned_data.get("host"),
            form.cleaned_data.get("host2"),
            form.cleaned_data.get("host3"),
        )
        if res.get("detail") is None:
            return super().form_valid(form)
        form.add_error("__all__", res.get("detail"))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        context["compute"] = compute
        return context

    def get_success_url(self):
        return reverse("admin_compute_storages", args=[self.kwargs.get("pk")])


class AdminComputeStorageView(AdminTemplateView):
    template_name = "admin/compute/storage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.get_storage(kwargs.get("pool"))
        messages.error(self.request, res.get("detail"))
        context["compute"] = compute
        context["form_start"] = FormStartAction()
        context["form_autostart"] = FormAutostartAction()
        context["storage_pool"] = res.get("storage")
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
            messages.error(self.request, res.get("detail"))
            context["form_start"] = form_start

        if form_autostart.is_valid():
            compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
            wvcomp = WebVirtCompute(compute.token, compute.hostname)
            res = wvcomp.set_storage_action(kwargs.get("pool"), form_autostart.cleaned_data.get("action"))
            if res.get("detail") is None:
                return redirect(self.request.get_full_path())
            messages.error(self.request, res.get("detail"))
            context["form_autostart"] = form_autostart

        return self.render_to_response(context)


class AdminComputeStorageDeleteView(AdminView):
    def get(self, request, *args, **kwargs):
        succes_url = redirect(request.get_full_path())
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.delete_storage(kwargs.get("pool"))
        if res.get("detail") is None:
            messages.success(request, "Storage successfuly deleted.")
            succes_url = redirect(reverse("admin_compute_storages", args=kwargs.get("pk")))
        else:
            messages.error(request, res.get("detail"))
        return succes_url


class AdminComputeStorageVolumeCreateView(AdminFormView):
    template_name = "admin/compute/volume_create.html"
    form_class = FormVolumeCreateAction

    def form_valid(self, form):
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.create_storage_volume(
            self.kwargs.get("pool"),
            form.cleaned_data.get("name"),
            form.cleaned_data.get("size"),
            form.cleaned_data.get("format"),
        )
        if res.get("detail") is not None:
            form.add_error("__all__", res.get("detail"))
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        context["compute"] = compute
        context["pool"] = self.kwargs.get("pool")
        return context

    def get_success_url(self):
        return reverse("admin_compute_storage", args=[self.kwargs.get("pk"), self.kwargs.get("pool")])


class AdminComputeStorageVolumeCloneView(AdminFormView):
    template_name = "admin/compute/volume_clone.html"
    form_class = FormVolumeCloneAction

    def form_valid(self, form):
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.action_storage_volume(
            self.kwargs.get("pool"), self.kwargs.get("vol"), "clone", form.cleaned_data.get("name")
        )
        if res.get("detail") is not None:
            form.add_error("__all__", res.get("detail"))
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        context["compute"] = compute
        context["pool"] = self.kwargs.get("pool")
        context["vol"] = self.kwargs.get("vol")
        return context

    def get_success_url(self):
        return reverse("admin_compute_storage", args=[self.kwargs.get("pk"), self.kwargs.get("pool")])


class AdminComputeStorageVolumeResizeView(AdminFormView):
    template_name = "admin/compute/volume_resize.html"
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
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        context["compute"] = compute
        context["pool"] = self.kwargs.get("pool")
        context["vol"] = self.kwargs.get("vol")
        return context

    def get_success_url(self):
        return reverse("admin_compute_storage", args=[self.kwargs.get("pk"), self.kwargs.get("pool")])


class AdminComputeStorageVolumeDeleteView(AdminView):
    def get(self, request, *args, **kwargs):
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.delete_storage_volume(kwargs.get("pool"), kwargs.get("vol"))
        if res.get("detail") is None:
            messages.success(request, "Volume successfuly deleted.")
        else:
            messages.error(request, res.get("detail"))
        return redirect(reverse("admin_compute_storage", args=[kwargs.get("pk"), kwargs.get("pool")]))


class AdminComputeNetworkCreateView(AdminFormView):
    template_name = "admin/compute/network_create.html"
    form_class = FormNetworkCreate

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.get_interfaces()
        form.fields["bridge_name"].choices = [
            (iface.get("name"), iface.get("name")) for iface in res.get("interfaces") if iface.get("type") == "bridge"
        ]
        return form

    def form_valid(self, form):
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.create_network(
            form.cleaned_data.get("name"), form.cleaned_data.get("bridge_name"), form.cleaned_data.get("openvswitch")
        )
        if res.get("detail") is None:
            return super().form_valid(form)
        form.add_error("__all__", res.get("detail"))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        context["compute"] = compute
        return context

    def get_success_url(self):
        return reverse("admin_compute_networks", args=[self.kwargs.get("pk")])


class AdminComputeNetworksView(AdminTemplateView):
    template_name = "admin/compute/networks.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.get_networks()
        messages.error(self.request, res.get("detail"))
        context["compute"] = compute
        context["networks"] = res.get("networks")
        return context


class AdminComputeNetworkView(AdminTemplateView):
    template_name = "admin/compute/network.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.get_network(kwargs.get("pool"))
        messages.error(self.request, res.get("detail"))
        context["compute"] = compute
        context["form_start"] = FormStartAction()
        context["form_autostart"] = FormAutostartAction()
        context["network_pool"] = res.get("network")
        return context

    def post(self, request, *args, **kwargs):
        form_start = FormStartAction(request.POST)
        form_autostart = FormAutostartAction(request.POST)
        context = self.get_context_data(*args, **kwargs)

        if form_start.is_valid():
            compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
            wvcomp = WebVirtCompute(compute.token, compute.hostname)
            res = wvcomp.set_network_action(kwargs.get("pool"), form_start.cleaned_data.get("action"))
            if res.get("detail") is None:
                return redirect(self.request.get_full_path())
            messages.error(self.request, res.get("detail"))
            context["form_start"] = form_start

        if form_autostart.is_valid():
            compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
            wvcomp = WebVirtCompute(compute.token, compute.hostname)
            res = wvcomp.set_network_action(kwargs.get("pool"), form_autostart.cleaned_data.get("action"))
            if res.get("detail") is None:
                return redirect(self.request.get_full_path())
            messages.error(self.request, res.get("detail"))
            context["form_autostart"] = form_autostart

        return self.render_to_response(context)


class AdminComputeNetworkDeleteView(AdminView):
    def get(self, request, *args, **kwargs):
        succes_url = redirect(request.get_full_path())
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.delete_network(kwargs.get("pool"))
        if res.get("detail") is None:
            messages.success(request, "Network successfuly deleted.")
            succes_url = redirect(reverse("admin_compute_networks", args=kwargs.get("pk")))
        else:
            messages.error(request, res.get("detail"))
        return succes_url


class AdminComputeSecretsView(AdminTemplateView):
    template_name = "admin/compute/secrets.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.get_secrets()
        messages.error(self.request, res.get("detail"))
        context["compute"] = compute
        context["secrets"] = res.get("secrets")
        return context


class AdminComputeSecretCreateView(AdminFormView):
    template_name = "admin/compute/secret_create.html"
    form_class = FormSecretCreateAction

    def form_valid(self, form):
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.create_secret(
            form.cleaned_data.get("ephemeral"),
            form.cleaned_data.get("private"),
            form.cleaned_data.get("type"),
            form.cleaned_data.get("data"),
        )
        if res.get("detail") is not None:
            form.add_error("__all__", res.get("detail"))
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        context["compute"] = compute
        return context

    def get_success_url(self):
        return reverse("admin_compute_secrets", args=self.kwargs.get("pk"))


class AdminComputeSecretValueView(AdminFormView):
    template_name = "admin/compute/secret_value.html"
    form_class = FormSecretValueAction

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.get_secret(self.kwargs.get("uuid"))
        secret = res.get("secret")
        form.fields["value"].initial = secret.get("value")
        return form

    def form_valid(self, form):
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.update_secret_value(self.kwargs.get("uuid"), form.cleaned_data.get("value"))
        if res.get("detail") is not None:
            form.add_error("__all__", res.get("detail"))
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        context["uuid"] = self.kwargs.get("uuid")
        context["compute"] = compute
        return context

    def get_success_url(self):
        return reverse("admin_compute_secrets", args=self.kwargs.get("pk"))


class AdminComputeSecretDeleteView(AdminView):
    def get(self, request, *args, **kwargs):
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.delete_secret(kwargs.get("uuid"))
        if res.get("detail") is None:
            messages.success(request, "Secret successfuly deleted.")
        else:
            messages.error(request, res.get("detail"))
        return redirect(reverse("admin_compute_secrets", args=kwargs.get("pk")))


class AdminComputeNwfiltersView(AdminTemplateView):
    template_name = "admin/compute/nwfilters.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.get_nwfilters()
        messages.error(self.request, res.get("detail"))
        context["compute"] = compute
        context["nwfilters"] = res.get("nwfilters")
        return context


class AdminComputeNwfilterCreateView(AdminFormView):
    template_name = "admin/compute/nwfilter_create.html"
    form_class = FormNwfilterCreateAction

    def form_valid(self, form):
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.create_nwfilter(form.cleaned_data.get("xml"))
        if res.get("detail") is not None:
            form.add_error("__all__", res.get("detail"))
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        context["compute"] = compute
        return context

    def get_success_url(self):
        return reverse("admin_compute_nwfilters", args=self.kwargs.get("pk"))


class AdminComputeNwfilterView(AdminTemplateView):
    template_name = "admin/compute/nwfilter.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        compute = get_object_or_404(Compute, pk=self.kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.view_nwfilter(kwargs.get("nfilter"))
        messages.error(self.request, res.get("detail"))
        context["compute"] = compute
        context["nwfilter"] = res.get("nwfilter")
        return context


class AdminComputeNwfilterDeleteView(AdminView):
    def get(self, request, *args, **kwargs):
        compute = get_object_or_404(Compute, pk=kwargs.get("pk"), is_deleted=False)
        wvcomp = WebVirtCompute(compute.token, compute.hostname)
        res = wvcomp.delete_nwfilter(kwargs.get("nfilter"))
        if res.get("detail") is None:
            messages.success(request, "NwFilter successfuly deleted.")
        else:
            messages.error(request, res.get("detail"))
        return redirect(reverse("admin_compute_nwfilters", args=[kwargs.get("pk")]))
