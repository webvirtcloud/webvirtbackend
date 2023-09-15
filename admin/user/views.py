from django.shortcuts import get_object_or_404

from account.models import User
from admin.mixins import AdminTemplateView


class AdminUserIndexView(AdminTemplateView):
    template_name = "admin/user/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = User.objects.filter(is_admin=False)
        return context


class AdminUserDataView(AdminTemplateView):
    template_name = "admin/user/user.html"

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.get_object()
        return context
