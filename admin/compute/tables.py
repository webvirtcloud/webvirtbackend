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
    id = tables.TemplateColumn(template_name="admin/compute/overview/id_column.html", verbose_name="ID")
    user = tables.TemplateColumn(template_name="admin/compute/overview/user_column.html", verbose_name="User")
    type = tables.Column(accessor="type", verbose_name="Type")
    size = tables.Column(accessor="size.description", verbose_name="Size")
    locked = tables.Column(accessor="is_locked", verbose_name="Locked")

    class Meta:
        model = Virtance
        fields = ("id", "user", "type", "size", "status", "locked", "created")
        template_name = "django_tables2/bootstrap.html"


class ComputeStoragesTable(tables.Table):
    name = tables.TemplateColumn(template_name="admin/compute/storages/name_column.html", verbose_name="Name")
    size = tables.TemplateColumn("{{ value|filesizeformat }}", verbose_name="Size")
    type = tables.TemplateColumn("{{ value|upper }}", verbose_name="Type")
    active = tables.Column(accessor="active", verbose_name="Active")
    volumes = tables.Column(accessor="volumes", verbose_name="Volumes")

    class Meta:
        template_name = "django_tables2/bootstrap_no_query.html"


class ComputeNetworksTable(tables.Table):
    name = tables.TemplateColumn(template_name="admin/compute/networks/name_column.html", verbose_name="Name")
    device = tables.Column(accessor="device", verbose_name="Device")
    active = tables.Column(accessor="active", verbose_name="Active")
    forward = tables.TemplateColumn("{{ value|capfirst }}", verbose_name="Forward")

    class Meta:
        template_name = "django_tables2/bootstrap_no_query.html"


class ComputeNwfilterTable(tables.Table):
    name = tables.TemplateColumn(template_name="admin/compute/nwfilters/name_column.html", verbose_name="Name")
    action = tables.TemplateColumn(
        template_name="admin/compute/nwfilters/action_column.html",
        verbose_name="Action",
        attrs={"th": {"data-type": "action"}, "td": {"data-type": "action"}},
        orderable=False,
    )

    class Meta:
        template_name = "django_tables2/bootstrap_no_query.html"


class ComputeSecretsTable(tables.Table):
    uuid = tables.TemplateColumn(template_name="admin/compute/secrets/uuid_column.html", verbose_name="Name")
    type = tables.Column(empty_values=(), verbose_name="Type")
    usage = tables.Column(accessor="usage", verbose_name="Usage")
    value = tables.Column(accessor="value", verbose_name="Value")
    action = tables.TemplateColumn(
        template_name="admin/compute/secrets/action_column.html",
        verbose_name="Action",
        attrs={"th": {"data-type": "action"}, "td": {"data-type": "action"}},
        orderable=False,
    )

    def render_type(self, value, record):
        if value == 0:
            return "volume"
        elif value == 1:
            return "iscsi"
        elif value == 2:
            return "ceph"
        return "unknown"

    class Meta:
        template_name = "django_tables2/bootstrap_no_query.html"


class ComputeStorageVolumesTable(tables.Table):
    name = tables.Column(accessor="name", verbose_name="Name")
    size = tables.TemplateColumn("{{ value|filesizeformat }}", verbose_name="Size")
    type = tables.TemplateColumn("{{ value|upper }}", verbose_name="Type")
    action = tables.TemplateColumn(
        template_name="admin/compute/storages/volumes/action_column.html",
        verbose_name="Action",
        attrs={"th": {"data-type": "action"}, "td": {"data-type": "action"}},
        orderable=False,
    )

    class Meta:
        template_name = "django_tables2/bootstrap_no_query.html"
