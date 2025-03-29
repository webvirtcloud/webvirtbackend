from django.conf import settings
from webvirtcloud.celery import app

from .models import DBaaS
from network.models import Network, IPAddress
from virtance.tasks import create_virtance
from virtance.provision import ansible_play
from virtance.utils import check_ssh_connect, decrypt_data, virtance_error


provision_tasks = [
    {
        "name": "Update APT",
        "action": {
            "module": "apt",
            "args": {
                "update_cache": True,
                "cache_valid_time": 3600,
            },
        },
    }
]


def provision_dbaas(host, private_key, tasks, dbaas_vars=None):
    task = None
    error = None

    res = ansible_play(private_key=private_key, hosts=host, tasks=tasks, extra_vars=dbaas_vars)

    if res.host_failed.items():
        for host, result in res.host_failed.items():
            task = result.task_name
            error = result._result["msg"]

    if res.host_unreachable.items():
        error = "Host unreachable."

    if res.host_ok.items():
        pass

    return error, task


@app.task
def create_dbaas(dbaas_id):
    dbaas = DBaaS.objects.get(id=dbaas_id)
    private_key = decrypt_data(dbaas.private_key)

    if create_virtance(dbaas.virtance.id, send_email=False):
        ipv4_public = IPAddress.objects.get(virtance=dbaas.virtance, network__type=Network.PUBLIC, is_float=False)
        ipv4_private = IPAddress.objects.get(virtance=dbaas.virtance, network__type=Network.PRIVATE, is_float=False)

        if check_ssh_connect(ipv4_public.address, private_key=private_key):
            
            dbaas_vars = {
                "ipv4_dbaas_access_list": settings.DBAAS_IPV4_ACCESS_LIST,
            }
            error, task = provision_dbaas(ipv4_public.address, private_key, provision_tasks, dbaas_vars=dbaas_vars)
            if error:
                error_message = error
                if task:
                    error_message = f"Task: {task}. Error: {error}"
                virtance_error(dbaas.virtance.id, error_message, event="dbaas_provision")
            else:
                dbaas.reset_event()
