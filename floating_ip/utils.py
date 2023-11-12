from .models import FloatIPError


def floatip_error(floatip_id, message, event=None):
    FloatIPError.objects.create(floatip_id=floatip_id, message=message, event=event)
