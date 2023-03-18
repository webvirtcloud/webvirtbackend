from base64 import b64encode
from random import choice
from string import digits, ascii_letters


def make_passwd(length=8):
    phrase = ''
    for _ in range(length):
        phrase += choice(f"{digits}{ascii_letters}")
    return phrase


def make_vnc_hash(vnc_password):
    return b64encode((f"{make_passwd(6)}{vnc_password}{make_passwd(8)}").encode())
