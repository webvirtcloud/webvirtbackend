import django_tables2 as tables

from floating_ip.models import FloatIP, FloatIPError


class FloatIPHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/floating_ip/id_column.html", verbose_name="ID")
    user = tables.TemplateColumn(template_name="admin/floating_ip/user_column.html", verbose_name="User")
    virtance = tables.TemplateColumn(
        template_name="admin/floating_ip/virtance_column.html", verbose_name="Virtance", orderable=False
    )

    class Meta:
        model = FloatIP
        fields = ("id", "user", "cidr", "virtance", "created")
        template_name = "django_tables2/bootstrap.html"


class FloatIPErrorTable(tables.Table):
    class Meta:
        model = FloatIPError
        template_name = "django_tables2/bootstrap_no_query.html"
        fields = ("event", "message", "created")
