import django_tables2 as tables

from network.models import Network


class NetworkHTMxTable(tables.Table):
    active = tables.TemplateColumn(
        template_name="django_tables2/is_active_column.html", verbose_name="Active", accessor="is_active"
    )
    action = tables.TemplateColumn(
        template_name="admin/network/action_column.html",
        verbose_name="Action",
        attrs={"th": {"data-type": "action"}, "td": {"data-type": "action"}},
        orderable=False,
    )
    region = tables.Column(verbose_name="Region", accessor="region.name")
    network = tables.TemplateColumn(
        template_name="admin/network/network_column.html", verbose_name="Network", accessor="cidr"
    )

    class Meta:
        model = Network
        fields = ("network", "region", "type", "active", "created")
        template_name = "django_tables2/bootstrap.html"
