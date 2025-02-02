import django_tables2 as tables

from floating_ip.models import FloatIP


class FloatIPHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/floating_ip/id_column.html", verbose_name="ID")
    user = tables.TemplateColumn(template_name="admin/floating_ip/user_column.html", verbose_name="User")
    virtance = tables.TemplateColumn(template_name="admin/floating_ip/virtance_column.html", verbose_name="Virtance")
    active = tables.TemplateColumn(
        template_name="django_tables2/is_active_column.html", verbose_name="Active", accessor="is_active"
    )

    def render_cidr(self, value, record):
        return record.cidr

    def render_virtance(self, value, record):
        return record.virtance

    class Meta:
        model = FloatIP
        fields = ("id", "user", "cidr", "virtance", "created")
        template_name = "django_tables2/bootstrap.html"
