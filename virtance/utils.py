from random import choice
from base64 import b64encode
from string import digits, ascii_letters

from .models import VirtanceError, VirtanceHistory


def make_passwd(length=8):
    phrase = ""
    for _ in range(length):
        phrase += choice(f"{digits}{ascii_letters}")
    return phrase


def make_vnc_hash(vnc_password, prefix_length=6, suffix_length=8):
    return b64encode(
        (f"{make_passwd(prefix_length)}{vnc_password}{make_passwd(suffix_length)}").encode()
    )


def virtance_history(virtance_id, user_id, message, event=None):
    VirtanceHistory.objects.create(virtance_id=virtance_id, user_id=user_id, message=message, event=event)


def virtance_error(virtance_id, message, event=None):
    VirtanceError.objects.create(virtance_id=virtance_id, message=message, event=event)

