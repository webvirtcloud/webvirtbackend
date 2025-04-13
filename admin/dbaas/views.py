from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from django.shortcuts import get_object_or_404

from admin.mixins import AdminView, AdminTemplateView
from dbaas.models import DBaaS

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
        return context
