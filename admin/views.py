from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from .forms import AdminAuthForm
from .mixins import LoginRequiredMixin


class AdminSingInView(LoginView):
    authentication_form = AdminAuthForm
    template_name = 'admin/sing_in.html'


class AdminSingOutView(LoginRequiredMixin, LogoutView):
    template_name = 'admin/sing_out.html'


class AdminIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'admin/index.html'
