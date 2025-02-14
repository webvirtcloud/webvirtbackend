import django_tables2 as tables

from virtance.models import Virtance, VirtanceError


class VirtanceHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/virtance/id_column.html", verbose_name="ID")
    user = tables.TemplateColumn(template_name="admin/virtance/user_column.html", verbose_name="User")
    compute = tables.TemplateColumn(template_name="admin/virtance/compute_column.html", verbose_name="Compute")
    status = tables.TemplateColumn(
        template_name="admin/virtance/status_column.html", verbose_name="Status", accessor="status"
    )
    size = tables.Column(verbose_name="Size", accessor="size.name")
    region = tables.Column(verbose_name="Region", accessor="region.name")

    def render_type(self, value, record):
        return record.type

    class Meta:
        model = Virtance
        fields = ("id", "user", "type", "size", "region", "compute", "status", "created")
        template_name = "django_tables2/bootstrap.html"


class VirtanceErrorTable(tables.Table):
    class Meta:
        model = VirtanceError
        template_name = "django_tables2/bootstrap_no_query.html"
        fields = ("event", "message", "created")
