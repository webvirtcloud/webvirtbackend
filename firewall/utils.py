from .models import FirewallError


def firewall_error(firewall_id, message, event=None):
    FirewallError.objects.create(firewall_id=firewall_id, message=message, event=event)
