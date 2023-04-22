from admin.mixins import AdminTemplateView


class AdminUserIndexView(AdminTemplateView):
    template_name = 'admin/user/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
