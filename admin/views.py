from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from .forms import AdminAuthForm


class AdminSingInView(LoginView):
    authentication_form = AdminAuthForm
    template_name = 'admin/sing_in.html'


class AdminSingOutView(LogoutView):
    template_name = 'admin/sing_out.html'


class AdminIndexView(TemplateView):
    template_name = 'admin/index.html'
