import django_tables2 as tables

from image.models import Image, ImageError


class ImageHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/image/id_column.html", verbose_name="ID")
    file_size = tables.TemplateColumn("{{ value|filesizeformat }}", verbose_name="File Size")
    disk_size = tables.TemplateColumn("{{ value|filesizeformat }}", verbose_name="Disk Size")

    class Meta:
        model = Image
        fields = ("id", "user", "type", "file_size", "disk_size", "created")
        template_name = "django_tables2/bootstrap.html"


class ImageErrorTable(tables.Table):
    class Meta:
        model = ImageError
        template_name = "django_tables2/bootstrap_no_query.html"
        fields = ("event", "message", "created")
