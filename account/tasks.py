from django.conf import settings

from webvirtcloud.celery import app
from webvirtcloud.email import send_email


@app.task
def email_confirm_register(url, recipient):
    subject = "WebVirtCloud confirm registration"
    context = {"confirm_url": url, "site_url": settings.SITE_URL}
    send_email(subject, recipient, context, "email/account-registration-confirm.html")
