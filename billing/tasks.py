from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from account.models import User
from billing.models import Balance, Invoice
from floating_ip.models import FloatIPCounter
from image.models import SnapshotCounter
from virtance.models import VirtanceCounter
from webvirtcloud.celery import app
from webvirtcloud.email import send_email


@app.task
def email_send_invoice(recipient, amount, period):
    subject = "WebVirtCloud Invoice"
    site_url = f"{settings.BASE_DOMAIN}"
    context = {"amount": amount, "period": period, "site_url": site_url}
    send_email(subject, recipient, context, "email/invoice.html")


@app.task
def make_monthly_invoice():
    now = timezone.now()
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0)
    prev_month = first_day_of_month - timezone.timedelta(days=1)
    start_of_month = prev_month.replace(day=1, hour=0, minute=0, second=0)
    end_of_month = prev_month.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Get all verified users
    for user in User.objects.filter(is_email_verified=True):
        invoice_exist = Invoice.objects.filter(user=user, create__gte=first_day_of_month).exists()

        if invoice_exist is False:
            total_usage = 0

            virtances_usage = (
                VirtanceCounter.objects.filter(
                    virtance__user=user,
                    started__gte=start_of_month,
                    stopped__lte=end_of_month,
                ).aggregate(total_amount=Sum("amount"))["total_amount"]
                or 0
            )
            total_usage += virtances_usage

            virtances_backup_usage = (
                VirtanceCounter.objects.filter(
                    virtance__user=user,
                    started__gte=start_of_month,
                    stopped__lte=end_of_month,
                ).aggregate(total_amount=Sum("backup_amount"))["total_amount"]
                or 0
            )
            total_usage += virtances_backup_usage

            virtances_license_usage = (
                VirtanceCounter.objects.filter(
                    virtance__user=user,
                    started__gte=start_of_month,
                    stopped__lte=end_of_month,
                ).aggregate(total_amount=Sum("license_amount"))["total_amount"]
                or 0
            )
            total_usage += virtances_license_usage

            snapshots_usage = (
                SnapshotCounter.objects.filter(
                    image__user=user,
                    started__gte=start_of_month,
                    stopped__lte=end_of_month,
                ).aggregate(total_amount=Sum("amount"))["total_amount"]
                or 0
            )
            total_usage += snapshots_usage

            floating_ips_usage = (
                FloatIPCounter.objects.filter(
                    floatip__user=user,
                    started__gte=start_of_month,
                    stopped__lte=end_of_month,
                ).aggregate(total_amount=Sum("amount"))["total_amount"]
                or 0
            )
            total_usage += floating_ips_usage

            # Create invoice
            invoice = Invoice.objects.create(user=user, amount=total_usage)

            # Update user balance
            Balance.objects.create(
                user=user, amount=invoice.amount, invoice=invoice, description=f"Invoice for {now.year}-{now.month}"
            )

            # Send invoice to user
            email_send_invoice(user.email, invoice.amount, f"{prev_month.year}-{prev_month.month}")
