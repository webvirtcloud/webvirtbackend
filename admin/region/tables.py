import django_tables2 as tables

from region.models import Region


class RegionHTMxTable(tables.Table):
    active = tables.TemplateColumn(
        template_name="django-tables2/is_active_column.html",
        verbose_name="Active", 
        accessor="is_active"
    )
    action = tables.TemplateColumn(
        template_name="admin/region/action_column.html",
        verbose_name="Action",
        attrs={"th": {"data-type": "action"}, "td": {"data-type": "action"}},
        orderable=False
    )

    class Meta:
        model = Region
        fields = ("slug", "name", "description", "active", "created")
        template_name = "django_tables2/bootstrap.html"
