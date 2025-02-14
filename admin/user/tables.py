import django_tables2 as tables

from account.models import User
from billing.models import Balance


class UserHTMxTable(tables.Table):
    active = tables.TemplateColumn(
        template_name="django_tables2/is_active_column.html", verbose_name="Active", accessor="is_active"
    )
    verified = tables.TemplateColumn(
        template_name="django_tables2/is_active_column.html", verbose_name="Verified", accessor="is_verified"
    )
    email = tables.TemplateColumn(template_name="admin/user/user_column.html", verbose_name="Email")

    name = tables.Column(empty_values=(), orderable=False)

    def render_name(self, value, record):
        return f"{record.first_name} {record.last_name}"

    class Meta:
        model = User
        fields = ("email", "name", "active", "verified", "created")
        template_name = "django_tables2/bootstrap.html"


class UserBillingHTMxTable(tables.Table):
    invoice = tables.Column(accessor="invoice_id", verbose_name="Invoice")
    created = tables.Column(accessor="create", verbose_name="Created")
    amount = tables.Column(empty_values=(), verbose_name="Amount")

    def render_amount(self, value, record):
        return f"${record.amount}"

    class Meta:
        model = Balance
        fields = ("amount", "invoice", "description", "created")
        template_name = "django_tables2/bootstrap.html"
