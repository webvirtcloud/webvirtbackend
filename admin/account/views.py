from django.urls import reverse_lazy
from crispy_forms.helper import FormHelper
from account.models import User
from admin.mixins import AdminUpdateView, AdminFormView
from .forms import FormChangePasswordAdmin


class AdminAccountProfileView(AdminUpdateView):
    template_name = 'admin/account/profile.html'
    template_name_suffix = "_form"
    model = User
    success_url = reverse_lazy('admin_profile')
    fields =  ["first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        super(AdminAccountProfileView, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super(AdminAccountProfileView, self).get_context_data(**kwargs)
        context['helper'] = self.helper
        return context


class AdminAccountChangePasswordView(AdminFormView):
    template_name = 'admin/account/change_password.html'
    form_class = FormChangePasswordAdmin
    success_url = reverse_lazy('admin_index')

    def get(self, request, *args, **kwargs):
        form = FormChangePasswordAdmin(request.user)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(request.user, request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
