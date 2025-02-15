from django.db.models import Q
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, RequestConfig

from .filters import ImageFilter
from .tables import ImageHTMxTable, ImageErrorTable
from image.models import Image, ImageError
from admin.mixins import AdminView, AdminTemplateView


class AdminImageIndexView(SingleTableMixin, FilterView, AdminView):
    table_class = ImageHTMxTable
    filterset_class = ImageFilter
    template_name = "admin/image/index.html"

    def get_queryset(self):
        return Image.objects.filter(Q(type=Image.BACKUP) | Q(type=Image.SNAPSHOT), is_deleted=False)

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name


class AdminImageDataView(AdminTemplateView):
    template_name = "admin/image/image.html"

    def get_object(self):
        return get_object_or_404(
            Image, Q(type=Image.BACKUP) | Q(type=Image.SNAPSHOT), pk=self.kwargs["pk"], is_deleted=False
        )

    def get_template_names(self):
        if self.request.htmx:
            return "django_tables2/table_partial.html"
        return self.template_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        image = self.get_object()

        image_errors = ImageError.objects.filter(image=image)
        image_errors_table = ImageErrorTable(image_errors)
        RequestConfig(self.request).configure(image_errors_table)

        context["image"] = image
        context["image_errors_table"] = image_errors_table
        return context


class AdminImageResetEventAction(AdminView):
    def get_object(self):
        return get_object_or_404(
            Image, Q(type=Image.BACKUP) | Q(type=Image.SNAPSHOT), pk=self.kwargs["pk"], is_deleted=False
        )

    def post(self, request, *args, **kwargs):
        image = self.get_object()
        image.reset_event()
        return redirect(reverse("admin_image_data", args=[kwargs.get("pk")]))
