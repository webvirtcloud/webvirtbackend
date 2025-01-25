import django_tables2 as tables

from region.models import Region


class RegionHTMxTable(tables.Table):
    active = tables.Column(verbose_name="Active", accessor="is_active")
    action = tables.TemplateColumn(
        template_name="admin/region/action_column.html",
        verbose_name="Action",
    )

    class Meta:
        model = Region
        fields = ("slug", "name", "description", "active", "created")
        template_name = "django_tables2/bootstrap.html"
