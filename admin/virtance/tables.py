import django_tables2 as tables

from virtance.models import Virtance


class VirtanceHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/virtance/id_column.html", verbose_name="ID")
    user = tables.TemplateColumn(template_name="admin/virtance/user_column.html", verbose_name="User")
    compute = tables.TemplateColumn(template_name="admin/virtance/compute_column.html", verbose_name="Compute")
    active = tables.TemplateColumn(
        template_name="django_tables2/is_active_column.html", verbose_name="Active", accessor="is_active"
    )
    size = tables.Column(verbose_name="Size", accessor="size.name")
    region = tables.Column(verbose_name="Region", accessor="region.name")

    def render_type(self, value, record):
        return record.type

    class Meta:
        model = Virtance
        fields = ("id", "user", "type", "size", "region", "compute", "active", "created")
        template_name = "django_tables2/bootstrap.html"
