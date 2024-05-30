from webvirtcloud.celery import app

from .models import LBaaS
from network.models import Network, IPAddress
from virtance.tasks import create_virtance
from virtance.utils import check_ssh_connect, decrypt_data
from virtance.provision import ansible_play


def provision_lbaas(host, private_key):
    tasks = {}
    private_key = decrypt_data(lbaas.virtance.private_key)

    ansible_play(private_key=private_key, hosts=host, tasks=tasks)


@app.task
def create_lbaas(lbaas_id):
    lbaas = LBaaS.objects.get(id=lbaas_id)
    private_key = decrypt_data(lbaas.virtance.private_key)
    ipaddr = IPAddress.objects.get(virtance=lbaas.virtance, network__type=Network.PUBLIC, is_float=False).address    

    if create_virtance(lbaas.virtance.id, send_email=False):
        if check_ssh_connect(ipaddr):
            provision_lbaas(ipaddr, private_key)

