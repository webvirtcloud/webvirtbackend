from .models import ImageError


def image_error(image_id, message, event=None):
    ImageError.objects.create(image_id=image_id, message=message, event=event)
