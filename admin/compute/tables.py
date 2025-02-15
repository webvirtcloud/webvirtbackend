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


class ComputeStoragesTable(tables.Table):
    name = tables.TemplateColumn(template_name="admin/compute/storage_name_column.html", verbose_name="Name")
    size = tables.TemplateColumn("{{ value|filesizeformat }}", verbose_name="Size")
    type = tables.TemplateColumn("{{ value|upper }}", verbose_name="Type")
    active = tables.Column(accessor="active", verbose_name="Active")
    volumes = tables.Column(accessor="volumes", verbose_name="Volumes")

    class Meta:
        model = Compute
        fields = ("name", "type", "size", "active", "volumes")
        template_name = "django_tables2/bootstrap_no_query.html"


class ComputeNetworksTable(tables.Table):
    name = tables.TemplateColumn(template_name="admin/compute/network_name_column.html", verbose_name="Name")
    device = tables.Column(accessor="device", verbose_name="Device")
    active = tables.Column(accessor="active", verbose_name="Active")
    forward = tables.TemplateColumn("{{ value|capfirst }}", verbose_name="Forward")

    class Meta:
        model = Compute
        fields = ("name", "device", "active", "forward")
        template_name = "django_tables2/bootstrap_no_query.html"


class ComputeNwfilterTable(tables.Table):
    name = tables.TemplateColumn(template_name="admin/compute/nwfilter_name_column.html", verbose_name="Name")
    action = tables.TemplateColumn(
        template_name="admin/compute/nwfilter_action_column.html",
        verbose_name="Action",
        attrs={"th": {"data-type": "action"}, "td": {"data-type": "action"}},
        orderable=False,
    )

    class Meta:
        model = Compute
        fields = ("name", "action")
        template_name = "django_tables2/bootstrap_no_query.html"
