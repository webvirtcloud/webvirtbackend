from admin.mixins import AdminTemplateView
from firewall.models import Firewall, Rule, FirewallVirtance, FirewallError


class AdminFirewallIndexView(AdminTemplateView):
    template_name = "admin/firewall/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        firewalls = Firewall.objects.filter(is_deleted=False)
        for firewall in firewalls:
            firewall.num_rule = len(Rule.objects.filter(firewall=firewall))
            firewall.num_virtance = len(FirewallVirtance.objects.filter(firewall=firewall))
        context["firewalls"] = firewalls
        return context
