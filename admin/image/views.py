from django.db.models import Q
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404

from image.models import Image
from admin.mixins import AdminView, AdminTemplateView


class AdminImageIndexView(AdminTemplateView):
    template_name = 'admin/image/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images'] = Image.objects.filter(Q(type=Image.BACKUP) | Q(type=Image.SNAPSHOT), is_deleted=False)
        return context


class AdminImageDataView(AdminTemplateView):
    template_name = 'admin/image/image.html'

    def get_object(self):
        return get_object_or_404(
            Image, Q(type=Image.BACKUP) | Q(type=Image.SNAPSHOT), pk=self.kwargs['pk'], is_deleted=False
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['image'] = self.get_object()
        return context


class AdminImageResetEventAction(AdminView):

    def get_object(self):
        return get_object_or_404(
            Image, Q(type=Image.BACKUP) | Q(type=Image.SNAPSHOT), pk=self.kwargs['pk'], is_deleted=False
        )
        
    def post(self, request, *args, **kwargs):
        image = self.get_object()
        image.reset_event()
        return redirect(reverse("admin_image_data", args=[kwargs.get("pk")]))
