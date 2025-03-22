import django_tables2 as tables

from size.models import DBMS


class DBMSHTMxTable(tables.Table):
    active = tables.TemplateColumn(
        template_name="django_tables2/is_active_column.html", verbose_name="Active", accessor="is_active"
    )
    action = tables.TemplateColumn(
        template_name="admin/dbms/action_column.html",
        verbose_name="Action",
        attrs={"th": {"data-type": "action"}, "td": {"data-type": "action"}},
        orderable=False,
    )

    class Meta:
        model = DBMS
        fields = ("slug", "name", "description", "active", "created")
        template_name = "django_tables2/bootstrap.html"
