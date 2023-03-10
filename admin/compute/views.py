from django.urls import reverse_lazy
from crispy_forms.helper import FormHelper
from .forms import FormCompute
from compute.models import Compute
from admin.mixins import AdminTemplateView, AdminFormView, AdminUpdateView, AdminDeleteView


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
