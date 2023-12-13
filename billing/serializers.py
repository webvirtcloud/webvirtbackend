from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from .models import Balance, Invoice
from account.models import User
from image.models import SnapshotCounter
from virtance.models import VirtanceCounter
from floating_ip.models import FloatIPCounter


class BalanceSerilizer(serializers.Serializer):
    account_balance = serializers.SerializerMethodField()
    month_to_date_usage = serializers.SerializerMethodField()
    month_to_date_balance = serializers.SerializerMethodField()
    generated_at = serializers.DateTimeField(default=timezone.now)

    class Meta:
        model = User
        fields = ("account_balance", "month_to_date_usage", "month_to_date_balance", "generated_at")

    def get_account_balance(self, obj):
        return Decimal(Balance.objects.filter(user=obj).aggregate(balance=Sum("amount"))["balance"] or 0)

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

        print(virtances_usage)

        # Calculate total usage
        month_to_date_usage += virtances_usage

        # Get snapshots usage
        snapshots_usage = (
            SnapshotCounter.objects.filter(
                image__user=obj,
                started__gte=start_of_month,
                stopped=None,
            ).aggregate(
                total_amount=Sum("amount")
            )["total_amount"]
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
            ).aggregate(
                total_amount=Sum("amount")
            )["total_amount"]
            or 0
        )

        # Calculate total usage
        month_to_date_usage += floating_ips_usage

        return Decimal(month_to_date_usage)

    def get_month_to_date_balance(self, obj):
        return Decimal(self.get_month_to_date_usage(obj) + self.get_account_balance(obj))


class BillingHistorySerilizer(serializers.Serializer):
    date = serializers.DateTimeField(source="create")
    type = serializers.SerializerMethodField()
    invoice = serializers.SerializerMethodField()

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

    class Meta:
        model = Invoice
        fields = ("uuid", "period", "amount")

    def get_period(self, obj):
        previous_month = obj.create.month - 1
        return previous_month.strftime("%Y-%m")
