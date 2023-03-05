from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from .forms import FormRegion
from region.models import Region


class AdminRegionIndexView(TemplateView):
    template_name = 'admin/region/index.html'


class AdminRegionCreateView(FormView):
    template_name = 'admin/region/create.html'
    form_class = FormRegion
    success_url = '/admin/region/'

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['regions'] = Region.objects.filter(is_deleted=False)
        return context
