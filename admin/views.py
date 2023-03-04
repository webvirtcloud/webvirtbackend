from django.urls import reverse_lazy
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from .forms import AdminAuthForm
from .mixins import LoginRequiredMixin


class AdminSingInView(LoginView):
    authentication_form = AdminAuthForm
    template_name = "admin/sign_in.html"
    redirect_authenticated_user=True

    def form_valid(self, form):
        user = form.get_user()
        if user.is_admin is True:
            login(self.request, user)
            return HttpResponseRedirect(self.get_success_url())
        return HttpResponseRedirect(reverse_lazy("admin_sign_in"))        


class AdminSingOutView(LoginRequiredMixin, LogoutView):
    template_name = "admin/sign_out.html"


class AdminIndexView(LoginRequiredMixin, TemplateView):
    admin_required = True
    template_name = "admin/index.html"
