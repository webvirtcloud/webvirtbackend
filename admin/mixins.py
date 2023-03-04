from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required


class LoginRequiredMixin:
    admin_required = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.user.is_active:
                return redirect(reverse_lazy("admin_sign_out"))

        if self.admin_required:
            if not request.user.is_admin:
                messages.error(request, "You don't have permission to access this page.")
                return redirect(reverse_lazy("admin_sign_out"))

        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)
