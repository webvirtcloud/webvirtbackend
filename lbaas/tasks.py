from webvirtcloud.celery import app

from .models import LBaaS
from network.models import Network, IPAddress
from virtance.tasks import create_virtance
from virtance.utils import check_ssh_connect, decrypt_data
from virtance.provision import ansible_play

provision_tasks = [
    {
        "name": "Template HAProxy configuration",
        "action": {
            "module": "template",
            "args": {
                "src": "ansible/lbaas/haproxy.cfg.j2",
                "dest": "/etc/haproxy/haproxy.cfg",
                "owner": "root",
                "group": "root",
                "mode": "0644",
            },
        },
    },
    {
        "name": "Restart haproxy service",
        "action": {
            "module": "systemd",
            "args": {"name": "haproxy", "state": "restarted", "enabled": "yes"},
        },
    },
    {
        "name": "Create iptables rules",
        "action": {
            "module": "template",
            "args": {
                "src": "ansible/lbaas/rules.v4.j2",
                "dest": "/etc/iptables/rules.v4",
                "owner": "root",
                "group": "root",
                "mode": "0644",
            },
        },
    },
    {
        "name": "Restart iptables service",
        "action": {
            "module": "systemd",
            "args": {
                "name": "netfilter-persistent",
                "state": "restarted",
                "enabled": "yes",
            },
        },
    },
    {
        "name": "Listen SSH on private IP address",
        "action": {
            "module": "replace",
            "args": {
                "dest": "/etc/ssh/sshd_config",
                "regexp": "#ListenAddress 0.0.0.0",
                "replace": "ListenAddress {{ ipv4_private_address }}",
            },
        },
    },
    {"name": "Restart SSH service", "action": {"module": "systemd", "args": {"name": "sshd", "state": "reloaded"}}},
]

reload_tasks = [
    {
        "name": "Template HAProxy configuration",
        "action": {
            "module": "template",
            "args": {
                "src": "ansible/lbaas/haproxy.cfg.j2",
                "dest": "/etc/haproxy/haproxy.cfg",
                "owner": "root",
                "group": "root",
                "mode": "0644",
            },
        },
    },
    {
        "name": "Restart haproxy service",
        "action": {
            "module": "systemd",
            "args": {"name": "haproxy", "state": "restarted", "enabled": "yes"},
        },
    },
]


def provision_lbaas(host, private_key, tasks, lbaas_vars=None):
    res = ansible_play(private_key=private_key, hosts=host, tasks=tasks, extra_vars=lbaas_vars)

    if res.host_failed.items():
        for host, result in res.host_failed.items():
            task = result.task_name
            error = result._result["msg"]

    if res.host_unreachable.items():
        error = "Host unreachable."

    if res.host_ok.items():
        pass


@app.task
def create_lbaas(lbaas_id):
    lbaas = LBaaS.objects.get(id=lbaas_id)
    if create_virtance(lbaas.virtance.id, send_email=False):
        ipaddr = IPAddress.objects.get(virtance=lbaas.virtance, network__type=Network.PUBLIC, is_float=False).address
        if check_ssh_connect(ipaddr):
            private_key = decrypt_data(lbaas.private_key)
            provision_lbaas(ipaddr, private_key, provision_tasks)
