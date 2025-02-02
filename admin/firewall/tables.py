import django_tables2 as tables

from firewall.models import Firewall, Rule, FirewallVirtance


class FirewallHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/firewall/id_column.html", verbose_name="ID")
    user = tables.TemplateColumn(template_name="admin/firewall/user_column.html", verbose_name="User")
    rules = tables.Column(empty_values=(), verbose_name="Rules", orderable=False)
    virtances = tables.Column(empty_values=(), verbose_name="Virtances", orderable=False)

    def render_rules(self, value, record):
        return Rule.objects.filter(firewall=record).count()

    def render_virtances(self, value, record):
        return FirewallVirtance.objects.filter(firewall=record).count()

    class Meta:
        model = Firewall
        fields = ("id", "user", "name", "rules", "virtances", "created")
        template_name = "django_tables2/bootstrap.html"
