import django_tables2 as tables

from firewall.models import Firewall


class FirewallHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/firewall/id_column.html", verbose_name="ID")
    user = tables.TemplateColumn(template_name="admin/firewall/user_column.html", verbose_name="User")
    active = tables.TemplateColumn(
        template_name="django_tables2/is_active_column.html", verbose_name="Active", accessor="is_active"
    )

    def render_rules(self, value, record):
        return record.num_rule

    def render_virtances(self, value, record):
        return record.num_virtance

    class Meta:
        model = Firewall
        fields = ("id", "user", "name", "rules", "virtances", "created")
        template_name = "django_tables2/bootstrap.html"
