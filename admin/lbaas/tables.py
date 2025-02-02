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
