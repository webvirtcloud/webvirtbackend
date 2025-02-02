import django_tables2 as tables

from image.models import Image


class TemplateHTMxTable(tables.Table):
    active = tables.TemplateColumn(
        template_name="django_tables2/is_active_column.html", verbose_name="Active", accessor="is_active"
    )
    action = tables.TemplateColumn(
        template_name="admin/template/action_column.html",
        verbose_name="Action",
        attrs={"th": {"data-type": "action"}, "td": {"data-type": "action"}},
        orderable=False,
    )

    def render_distribution(self, value, record):
        return record.distribution

    def render_type(self, value, record):
        return record.type

    class Meta:
        model = Image
        fields = ("slug", "name", "distribution", "description", "type", "active", "created")
        template_name = "django_tables2/bootstrap.html"
