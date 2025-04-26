import django_tables2 as tables

from firewall.models import FirewallError
from floating_ip.models import FloatIPError
from image.models import ImageError
from virtance.models import VirtanceError


class IssueVirtanceHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/issue/virtance/id_column.html", verbose_name="ID")

    class Meta:
        model = VirtanceError
        fields = ("id", "event", "message", "created")
        template_name = "django_tables2/bootstrap.html"


class IssueImageHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/issue/image/id_column.html", verbose_name="ID")

    class Meta:
        model = ImageError
        fields = ("id", "event", "message", "created")
        template_name = "django_tables2/bootstrap.html"


class IssueFirewallHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/issue/firewall/id_column.html", verbose_name="ID")

    class Meta:
        model = FirewallError
        fields = ("id", "event", "message", "created")
        template_name = "django_tables2/bootstrap.html"


class IssueFloadIPHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/issue/floatip/id_column.html", verbose_name="ID")

    class Meta:
        model = FloatIPError
        fields = ("id", "event", "message", "created")
        template_name = "django_tables2/bootstrap.html"
