import django_tables2 as tables

from image.models import Image


class ImageHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/image/id_column.html", verbose_name="ID")
    active = tables.TemplateColumn(
        template_name="django_tables2/is_active_column.html", verbose_name="Active", accessor="is_active"
    )
    file_size = tables.TemplateColumn("{{ value|filesizeformat }}", verbose_name="File Size")
    disk_size = tables.TemplateColumn("{{ value|filesizeformat }}", verbose_name="Disk Size")

    class Meta:
        model = Image
        fields = ("id", "user", "type", "event", "file_size", "disk_size", "active", "created")
        template_name = "django_tables2/bootstrap.html"
