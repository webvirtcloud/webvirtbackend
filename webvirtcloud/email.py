from django.conf import settings
from django.utils.html import strip_tags
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def email_confirm_register(url, recipient):
    context = {'confirm_url': url}

    subject = 'WebVirtCloud confirm registration'
    from_email = settings.EMAIL_FROM
    html_message = render_to_string('confirm_register.html', context)

    email = EmailMessage(subject, strip_tags(html_message), from_email, [recipient])
    email.content_subtype = 'html'
    email.attach_alternative(html_message, "text/html")

    email.send()
