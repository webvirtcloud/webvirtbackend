import django_tables2 as tables

from dbaas.models import DBaaS


class DBaaSHTMxTable(tables.Table):
    id = tables.TemplateColumn(template_name="admin/dbaas/id_column.html", verbose_name="ID")
    user = tables.TemplateColumn(template_name="admin/dbaas/user_column.html", verbose_name="User")
    dbms = tables.Column(accessor="dbms.name", verbose_name="DBMS")

    class Meta:
        model = DBaaS
        fields = ("id", "user", "name", "dbms", "created")
        template_name = "django_tables2/bootstrap.html"
