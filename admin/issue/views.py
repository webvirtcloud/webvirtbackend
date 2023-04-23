from django.utils import timezone

from virtance.models import VirtanceError
from admin.mixins import AdminTemplateView


class AdminIssueIndexView(AdminTemplateView):
    template_name = 'admin/issue/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AdminIssueVirtanceView(AdminTemplateView):
    template_name = 'admin/issue/virtance.html'

    def get_context_data(self, **kwargs):
        thirty_days_ago = (timezone.now() - timezone.timedelta(days=30))
        context = super().get_context_data(**kwargs)
        context["virtace_errors"] = VirtanceError.objects.filter(created__gte=thirty_days_ago)
        return context
