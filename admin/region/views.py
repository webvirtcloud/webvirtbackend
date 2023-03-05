from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView, UpdateView, DeleteView
from .forms import FormRegion
from region.models import Region
from admin.mixins import LoginRequiredMixin

class AdminRegionIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'admin/region/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['regions'] = Region.objects.filter(is_deleted=False)
        return context


class AdminRegionCreateView(LoginRequiredMixin, FormView):
    template_name = 'admin/region/create.html'
    form_class = FormRegion
    success_url = reverse_lazy('admin_region_index')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class AdminRegionUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'admin/region/update.html'
    template_name_suffix = "_form"
    model = Region
    success_url = reverse_lazy('admin_region_index')
    fields = ["name", "slug", "description", "is_active"]

class AdminRegionDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'admin/region/delete.html'
    model = Region
    success_url = reverse_lazy('admin_region_index')

    def delete(self, request, *args, **kwargs):
        region = self.get_object()
        region.delete()
        return super(self).delete(request, *args, **kwargs)
