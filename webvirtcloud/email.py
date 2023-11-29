import socket
from django.conf import settings
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_email(subject, recipient, context, template):
    subject = subject if subject else "WebVirtCloud"
    from_email = settings.EMAIL_FROM
    html_message = render_to_string(template, context)

    try:
        send_mail(
            subject, strip_tags(html_message), from_email, [recipient], fail_silently=True, html_message=html_message
        )
    except socket.error:
        pass
