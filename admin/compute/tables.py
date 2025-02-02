import django_tables2 as tables

from compute.models import Compute


class ComputeHTMxTable(tables.Table):
    active = tables.TemplateColumn(
        template_name="django_tables2/is_active_column.html", verbose_name="Active", accessor="is_active"
    )
    action = tables.TemplateColumn(
        template_name="admin/size/action_column.html",
        verbose_name="Action",
        attrs={"th": {"data-type": "action"}, "td": {"data-type": "action"}},
        orderable=False,
    )
    region = tables.Column(accessor="region.name", verbose_name="Region")

    def render_arch(self, value, record):
        return record.arch

    class Meta:
        model = Compute
        fields = ("name", "hostname", "arch", "description", "region", "active", "created")
        template_name = "django_tables2/bootstrap.html"
