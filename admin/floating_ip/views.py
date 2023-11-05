from floating_ip.models import FloatIP
from admin.mixins import AdminTemplateView



class AdminFloatIPIndexView(AdminTemplateView):
    template_name = "admin/floating_ip/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["floating_ips"] = FloatIP.objects.filter(is_deleted=False)
        return context
