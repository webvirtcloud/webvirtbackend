from firewall.models import Firewall
from admin.mixins import AdminTemplateView


class AdminFirewallIndexView(AdminTemplateView):
    template_name = "admin/firewall/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["firewalls"] = Firewall.objects.filter(is_deleted=False)
        return context
