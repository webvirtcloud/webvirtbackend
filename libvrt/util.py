import random
import libvirt
import paramiko
from time import sleep
from base64 import b64decode
from passlib.hash import sha512_crypt
from xml.etree import ElementTree as ET
from string import ascii_letters, digits


def is_kvm_available(xml):
    tree = ET.fromstring(xml)
    for dom in tree.findall('guest/arch/domain'):
        if 'kvm' in dom.get('type'):
            return True
    return False


def randomMAC():
    """
    Generate a random MAC address.

    """
    # Qemu mask
    oui = [0x52, 0x54, 0x00]

    mac = oui + [
        random.randint(0x00, 0xFF),
        random.randint(0x00, 0xFF),
        random.randint(0x00, 0xFF),
    ]
    return ':'.join("%02x" % x for x in mac)


def randomUUID():
    """
    Generate a random UUID.

    """
    u = [random.randint(0, 255) for _ in range(0, 16)]
    return "-".join(["%02x" * 4, "%02x" * 2, "%02x" * 2, "%02x" * 2, "%02x" * 6]) % tuple(u)


def get_max_vcpus(conn, cpu_type=None):
    """
    @param conn: libvirt connection to poll for max possible vcpus
    @type type: optional guest type (kvm, etc.)

    """
    if cpu_type is None:
        cpu_type = conn.getType()
    try:
        m = conn.getMaxVcpus(cpu_type.lower())
    except libvirt.libvirtError:
        m = 32
    return m


def xml_escape(data):
    """
    Replaces chars ' " < > & with xml safe counterparts

    """
    if data is None:
        return None

    data = data.replace("&", "&amp;")
    data = data.replace("'", "&apos;")
    data = data.replace("\"", "&quot;")
    data = data.replace("<", "&lt;")
    data = data.replace(">", "&gt;")
    return data


def compareMAC(p, q):
    """
    Compare two MAC addresses.

    """
    pa = p.split(":")
    qa = q.split(":")

    if len(pa) != len(qa):
        if p > q:
            return 1
        else:
            return -1

    for i in range(len(pa)):
        n = int(pa[i], 0x10) - int(qa[i], 0x10)
        if n > 0:
            return 1
        elif n < 0:
            return -1
    return 0


def get_xml_data(xml, path=None, element=None):
    res = ''
    if not path and not element:
        return ''

    tree = ET.fromstring(xml)
    if path:
        child = tree.find(path)
        if child is not None:
            if element:
                res = child.get(element)
            else:
                res = child.text
    else:
        res = tree.get(element)
    return res


def get_xml_findall(xml, string):
    tree = ET.fromstring(xml)
    return tree.findall(string)


def pretty_megabytes(val):
    return "%dMb" % (int(val) / (1024.0**2))


def pretty_gigabytes(val):
    return "%dGb" % (int(val) / (1024.0**3))


def pretty_bytes(val):
    val = int(val)
    if val > (1024**3):
        return "%2.2fGb" % (val / (1024.0**3))
    else:
        return "%2.2fMb" % (val / (1024.0**2))


def gen_password(length=22, symbols=False):
    simple_symbols = ''
    if symbols:
        simple_symbols = '!@#$%^&*()_+[]-=:;{}?|<>'
    password = ''.join([random.choice(ascii_letters + simple_symbols + digits) for _ in range(length)])
    return password


def decode_password(enc, salt=8):
    password = b64decode(enc)[salt:].decode()
    return password


def password_to_hash(password):
    salt = gen_password(8)
    password_hash = sha512_crypt.encrypt(password, salt=salt, rounds=5000)
    return password_hash


def check_ssh_connection(host, password, username='root', timeout=300):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    for i in range(timeout):
        try:
            ssh.connect(
                host,
                username=username,
                password=password,
                allow_agent=False,
                look_for_keys=False,
            )
            ssh.close()
            return True
        except Exception:
            sleep(1)

    return False
