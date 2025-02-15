import django_tables2 as tables

from compute.models import Compute
from virtance.models import Virtance


class ComputeHTMxTable(tables.Table):
    name = tables.TemplateColumn(template_name="admin/compute/name_column.html", verbose_name="Namw", accessor="name")
    active = tables.TemplateColumn(
        template_name="django_tables2/is_active_column.html", verbose_name="Active", accessor="is_active"
    )
    action = tables.TemplateColumn(
        template_name="admin/compute/action_column.html",
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


class ComputeOverviewHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/compute/virtance_id_column.html", verbose_name="ID")
    user = tables.TemplateColumn(template_name="admin/compute/user_column.html", verbose_name="User")
    size = tables.Column(accessor="size.name", verbose_name="Size")
    region = tables.Column(accessor="region.name", verbose_name="Region")
    locked = tables.Column(accessor="is_locked", verbose_name="Locked")

    class Meta:
        model = Virtance
        fields = ("id", "user", "size", "region", "status", "locked", "created")
        template_name = "django_tables2/bootstrap.html"
