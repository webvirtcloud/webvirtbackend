import django_tables2 as tables

from lbaas.models import LBaaS, LBaaSVirtance, LBaaSForwadRule


class LBaaSHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/lbaas/id_column.html", verbose_name="ID")
    user = tables.TemplateColumn(template_name="admin/lbaas/user_column.html", verbose_name="User")
    rules = tables.Column(empty_values=(), verbose_name="Rules", orderable=False)
    virtances = tables.Column(empty_values=(), verbose_name="Virtances", orderable=False)

    def render_rules(self, value, record):
        return LBaaSForwadRule.objects.filter(lbaas=record, is_deleted=False).count()

    def render_virtances(self, value, record):
        return LBaaSVirtance.objects.filter(lbaas=record, is_deleted=False).count()

    class Meta:
        model = LBaaS
        fields = ("id", "user", "name", "rules", "virtances", "created")
        template_name = "django_tables2/bootstrap.html"


class HealthTable(tables.Table):
    protocol = tables.Column(verbose_name="Protocol")
    port = tables.Column(verbose_name="Port")
    path = tables.Column(verbose_name="Path")
    interval = tables.Column(verbose_name="Interval")
    timeout = tables.Column(verbose_name="Timeout")
    healthy = tables.Column(verbose_name="Healthy")
    unhealthy = tables.Column(verbose_name="Unhealthy")

    def render_protocol(self, value, record):
        return record.get("protocol").upper()

    def render_path(self, value, record):
        if record.get("protocol") == "http":
            return record.get("path")
        return "N/A"

    class Meta:
        template_name = "django_tables2/bootstrap_no_query.html"


class RulesTable(tables.Table):

    class Meta:
        model = LBaaSForwadRule
        fields = ("id", "entry_protocol", "entry_port", "target_protocol", "target_port", "created")
        template_name = "django_tables2/bootstrap_no_query.html"


class VirtancesTable(tables.Table):
    virtance = tables.TemplateColumn(template_name="admin/lbaas/virtance_column.html", verbose_name="Virtance")

    class Meta:
        model = LBaaSVirtance
        fields = ("id", "virtance", "created")
        template_name = "django_tables2/bootstrap_no_query.html"
