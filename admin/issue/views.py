from django.utils import timezone

from image.models import ImageError
from virtance.models import VirtanceError
from admin.mixins import AdminTemplateView


class AdminIssueIndexView(AdminTemplateView):
    template_name = "admin/issue/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AdminIssueVirtanceView(AdminTemplateView):
    template_name = "admin/issue/virtance.html"

    def get_context_data(self, **kwargs):
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        context = super().get_context_data(**kwargs)
        context["virtances_errors"] = VirtanceError.objects.filter(
            virtance__is_deleted=False, created__gte=thirty_days_ago
        )
        return context


class AdminIssueImageView(AdminTemplateView):
    template_name = "admin/issue/image.html"

    def get_context_data(self, **kwargs):
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        context = super().get_context_data(**kwargs)
        context["images_errors"] = ImageError.objects.filter(image__is_deleted=False, created__gte=thirty_days_ago)
        return context
