from random import choice
from base64 import b64encode
from django.conf import settings
from string import digits, ascii_letters

from .models import VirtanceError, VirtanceHistory


NOVNC_PASSWD_PREFIX = settings.NOVNC_PASSWD_PREFIX_LENGHT
NOVNC_PASSWD_SUFFIX = settings.NOVNC_PASSWD_SUFFIX_LENGHT


def make_passwd(length=8):
    phrase = ""
    for _ in range(length):
        phrase += choice(f"{digits}{ascii_letters}")
    return phrase


def make_vnc_hash(vnc_password, prefix_length=NOVNC_PASSWD_PREFIX, suffix_length=NOVNC_PASSWD_SUFFIX):
    return b64encode(
        (f"{make_passwd(prefix_length)}{vnc_password}{make_passwd(suffix_length)}").encode()
    )


def virtance_history(virtance_id, user_id, message, event=None):
    VirtanceHistory.objects.create(virtance_id=virtance_id, user_id=user_id, message=message, event=event)


def virtance_error(virtance_id, message, event=None):
    VirtanceError.objects.create(virtance_id=virtance_id, message=message, event=event)
