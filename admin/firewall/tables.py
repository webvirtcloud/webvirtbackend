import django_tables2 as tables

from firewall.models import Firewall, Rule, FirewallVirtance, FirewallError


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


class FirewallRuleTable(tables.Table):
    type = tables.Column(empty_values=(), verbose_name="Type")
    ports = tables.Column(empty_values=(), verbose_name="Ports")

    def render_type(self, value, record):
        if record.is_system == True:
            return "System"
        return "User"

    def render_ports(self, value, record):
        if value == "0":
            return "All"
        return value

    class Meta:
        model = Rule
        template_name = "django_tables2/bootstrap_no_query.html"
        fields = ("direction", "protocol", "ports", "action", "type", "created")


class FirewallVirtanceTable(tables.Table):
    attached = tables.TemplateColumn(template_name="admin/firewall/virtance_column.html", verbose_name="Attached")

    class Meta:
        model = FirewallVirtance
        template_name = "django_tables2/bootstrap_no_query.html"
        fields = ("virtance", "created")


class FirewallErrorTable(tables.Table):
    class Meta:
        model = FirewallError
        template_name = "django_tables2/bootstrap_no_query.html"
        fields = ("event", "message", "created")
