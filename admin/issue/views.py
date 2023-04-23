from admin.mixins import AdminTemplateView


class AdminIssueIndexView(AdminTemplateView):
    template_name = 'admin/issue/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
