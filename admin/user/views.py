from django.urls import reverse
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from crispy_forms.helper import FormHelper

from account.models import User
from admin.user.forms import FormUser
from admin.mixins import AdminTemplateView, AdminFormView, AdminUpdateView


class AdminUserIndexView(AdminTemplateView):
    template_name = "admin/user/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = User.objects.filter(is_admin=False)
        return context


class AdminUserCreateView(AdminFormView):
    template_name = "admin/user/create.html"
    form_class = FormUser
    success_url = reverse_lazy("admin_user_index")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class AdminUserUpdateView(AdminUpdateView):
    template_name = "admin/user/update.html"
    template_name_suffix = "_form"
    model = User
    fields = ["first_name", "last_name", "is_active"]

    def __init__(self, *args, **kwargs):
        super(AdminUserUpdateView, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(AdminUserUpdateView, self).get_context_data(**kwargs)
        context["helper"] = self.helper
        return context
    
    def get_success_url(self):
        return reverse("admin_user_data", args=[self.kwargs.get("pk")])


class AdminUserDataView(AdminTemplateView):
    template_name = "admin/user/user.html"

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.get_object()
        return context
