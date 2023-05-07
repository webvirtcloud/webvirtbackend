from admin.mixins import AdminTemplateView

from account.models import User


class AdminUserIndexView(AdminTemplateView):
    template_name = 'admin/user/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.filter(is_admin=False)
        return context
