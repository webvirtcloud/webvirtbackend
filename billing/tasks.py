from django.db.models import Sum
from django.conf import settings
from django.utils import timezone

from webvirtcloud.celery import app
from webvirtcloud.email import send_email
from account.models import User
from billing.models import Invoice
from image.models import SnapshotCounter
from virtance.models import VirtanceCounter
from floating_ip.models import FloatIPCounter


@app.task
def email_send_invoice(recipient, amount, period):
    subject = f"WebVirtCloud Invoice"
    site_url = f"{settings.CLIENT_URL}"
    context = {"amount": amount, "period": period, "site_url": site_url}
    send_email(subject, recipient, context, "email/invoice.html")


@app.task
def make_monthly_invoice():
    now = timezone.now()
    
    # Check if it is the first day of the month
    if now.day == 1:
        prev_month = now - timezone.timedelta(days=1)
        start_of_month = prev_month.replace(day=1, hour=0, minute=0, second=0)
        end_of_month = prev_month.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get all verified users
        for user in User.objects.filter(is_email_verified=True):
            total_usage = 0
            
            # Get virtance usage
            virtances_usage = VirtanceCounter.objects.filter(
                virtance__user=user,
                started__gte=start_of_month,
                stopped__lte=end_of_month,
            ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
            
            # Calculate total usage
            total_usage += virtances_usage
            
            # Get snapshots usage
            snapshots_usage = SnapshotCounter.objects.filter(
                image__user=user,
                started__gte=start_of_month,
                stopped__lte=end_of_month,
            ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0

            # Calculate total usage
            total_usage += snapshots_usage

            # Get floating ip usage
            floating_ips_usage = FloatIPCounter.objects.filter(
                floating_ip__user=user,
                started__gte=start_of_month,
                stopped__lte=end_of_month,
            ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0

            # Calculate total usage
            total_usage += floating_ips_usage

            # Create invoice
            invoice = Invoice.objects.create(
                user=user,
                amount=total_usage
            )
            
            # Send invoice to user
            email_send_invoice(user.email, invoice.amount, f"{now.year}-{now.month}")
