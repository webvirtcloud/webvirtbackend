from django.views.generic import TemplateView


class AdminRegionIndexView(TemplateView):
    template_name = 'admin/region/index.html'
