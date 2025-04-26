from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from account.models import User
from floating_ip.models import FloatIPCounter
from image.models import SnapshotCounter
from virtance.models import VirtanceCounter

from .models import Balance, Invoice


class BalanceSerilizer(serializers.Serializer):
    account_balance = serializers.SerializerMethodField()
    month_to_date_usage = serializers.SerializerMethodField()
    month_to_date_balance = serializers.SerializerMethodField()
    generated_at = serializers.DateTimeField(default=timezone.now)

    class Meta:
        model = User
        fields = ("account_balance", "month_to_date_usage", "month_to_date_balance", "generated_at")

    def get_account_balance(self, obj):
        balance = Balance.objects.filter(user=obj).aggregate(balance=Sum("amount"))["balance"] or 0
        return f"{balance:.2f}"

    def get_month_to_date_usage(self, obj):
        month_to_date_usage = 0
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0)

        # Get virtance usage
        virtances_usage = (
            VirtanceCounter.objects.filter(
                virtance__user=obj,
                started__gte=start_of_month,
                stopped=None,
            ).aggregate(total_amount=Sum("amount"))["total_amount"]
            or 0
        )

        # Calculate total usage
        month_to_date_usage += virtances_usage

        # Get snapshots usage
        snapshots_usage = (
            SnapshotCounter.objects.filter(
                image__user=obj,
                started__gte=start_of_month,
                stopped=None,
            ).aggregate(total_amount=Sum("amount"))["total_amount"]
            or 0
        )

        # Calculate total usage
        month_to_date_usage += snapshots_usage

        # Get floating ip usage
        floating_ips_usage = (
            FloatIPCounter.objects.filter(
                floatip__user=obj,
                started__gte=start_of_month,
                stopped=None,
            ).aggregate(total_amount=Sum("amount"))["total_amount"]
            or 0
        )

        # Calculate total usage
        month_to_date_usage += floating_ips_usage

        return f"{month_to_date_usage:.2f}"

    def get_month_to_date_balance(self, obj):
        balance = Balance.objects.filter(user=obj).aggregate(balance=Sum("amount"))["balance"] or 0
        result = Decimal(balance) + Decimal(self.get_month_to_date_usage(obj))
        return f"{result:.2f}"


class BillingHistorySerilizer(serializers.Serializer):
    date = serializers.DateTimeField(source="create")
    type = serializers.SerializerMethodField()
    invoice = serializers.SerializerMethodField()
    description = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Balance
        fields = ("amount", "description", "invoice", "date", "type")

    def get_type(self, obj):
        if obj.invoice:
            return "Invoice"
        return "Payment"

    def get_invoice(self, obj):
        if obj.invoice:
            return obj.invoice.uuid
        return None


class InvoiceSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    period = serializers.SerializerMethodField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField(source="create")

    class Meta:
        model = Invoice
        fields = ("uuid", "period", "amount", "created_at")

    def get_period(self, obj):
        first_day_prev_month = obj.create.replace(day=1) - timezone.timedelta(days=1)
        return first_day_prev_month.strftime("%Y-%m")
