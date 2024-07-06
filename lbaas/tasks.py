from webvirtcloud.celery import app

from .models import LBaaS, LBaaSForwadRule, LBaaSVirtance
from network.models import Network, IPAddress
from virtance.tasks import create_virtance, delete_virtance
from virtance.provision import ansible_play
from virtance.utils import check_ssh_connect, decrypt_data, virtance_error


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
        "name": "Change prometheus listen address",
        "action": {
            "module": "replace",
            "args": {
                "dest": "/etc/default/prometheus",
                "regexp": 'ARGS=""',
                "replace": 'ARGS="--web.listen-address={{ ipv4_private_address }}:9090"',
            },
        },
    },
    {
        "name": "Restart prometheus service",
        "action": {"module": "systemd", "args": {"name": "prometheus", "state": "reloaded"}},
    },
    {
        "name": "Disable systemd-resolved service",
        "action": {
            "module": "systemd",
            "args": {"name": "systemd-resolved", "state": "stopped", "enabled": "no"},
        },
    },
    {
        "name": "Remove resolv.conf symlink",
        "action": {
            "module": "file",
            "args": {
                "path": "/etc/resolv.conf",
                "state": "absent",
            },
        },
    },
    {
        "name": "Create resolv.conf",
        "action": {
            "module": "template",
            "args": {
                "src": "ansible/lbaas/resolv.conf.j2",
                "dest": "/etc/resolv.conf",
                "owner": "root",
                "group": "root",
                "mode": "0644",
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
    task = None
    error = None

    res = ansible_play(private_key=private_key, hosts=host, tasks=tasks, extra_vars=lbaas_vars)

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
def create_lbaas(lbaas_id):
    lbaas = LBaaS.objects.get(id=lbaas_id)
    private_key = decrypt_data(lbaas.private_key)

    if create_virtance(lbaas.virtance.id, send_email=False):
        ipv4_public_address = IPAddress.objects.get(
            virtance=lbaas.virtance, network__type=Network.PUBLIC, is_float=False
        ).address
        ipv4_private_address = IPAddress.objects.get(
            virtance=lbaas.virtance, network__type=Network.PRIVATE, is_float=False
        ).address

        if check_ssh_connect(ipv4_public_address, private_key=private_key):
            health = {
                "check_protocol": lbaas.check_protocol,
                "check_port": lbaas.check_port,
                "check_path": lbaas.check_path,
                "check_interval_seconds": lbaas.check_interval_seconds,
                "check_timeout_seconds": lbaas.check_timeout_seconds,
                "check_unhealthy_threshold": lbaas.check_unhealthy_threshold,
                "check_healthy_threshold": lbaas.check_healthy_threshold,
            }

            forwarding_rules = []
            for rule in LBaaSForwadRule.objects.filter(lbaas=lbaas, is_deleted=False):
                forwarding_rules.append(
                    {
                        "entry_port": rule.entry_port,
                        "entry_protocol": rule.entry_protocol,
                        "target_port": rule.target_port,
                        "target_protocol": rule.target_protocol,
                    }
                )

            sticky_sessions = {}
            if sticky_sessions:
                sticky_sessions = {
                    "cookie_ttl": lbaas.sticky_sessions_cookie_ttl,
                    "cookie_name": lbaas.sticky_sessions_cookie_name,
                }

            virtances = []
            for l_v in LBaaSVirtance.objects.filter(lbaas=lbaas, is_deleted=False):
                ipv4_address = IPAddress.objects.get(
                    virtance=l_v.virtance, network__type=Network.PRIVATE, is_float=False
                ).address
                virtances.append(
                    {
                        "virtance_id": l_v.virtance.id,
                        "ipv4_address": ipv4_address,
                    }
                )

            lbaas_vars = {
                "health": health,
                "virtances": virtances,
                "sticky_sessions": sticky_sessions,
                "forwarding_rules": forwarding_rules,
                "redirect_to_https": lbaas.redirect_http_to_https,
                "ipv4_public_address": ipv4_private_address,
                "ipv4_private_address": ipv4_private_address,
            }
            error, task = provision_lbaas(ipv4_public_address, private_key, provision_tasks, lbaas_vars=lbaas_vars)
            if error:
                error_message = error
                if task:
                    error_message = f"Task: {task}. Error: {error}"
                virtance_error(lbaas.virtance.id, error_message, event="lbaas_provision")
            else:
                lbaas.reset_events()


@app.task
def reload_lbaas(lbaas_id):
    lbaas = LBaaS.objects.get(id=lbaas_id)
    private_key = decrypt_data(lbaas.private_key)
    ipv4_private_address = IPAddress.objects.get(
        virtance=lbaas.virtance, network__type=Network.PRIVATE, is_float=False
    ).address

    if check_ssh_connect(lbaas.ipv4_private_address, private_key=private_key):
        health = {
            "check_protocol": lbaas.check_protocol,
            "check_port": lbaas.check_port,
            "check_path": lbaas.check_path,
            "check_interval_seconds": lbaas.check_interval_seconds,
            "check_timeout_seconds": lbaas.check_timeout_seconds,
            "check_unhealthy_threshold": lbaas.check_unhealthy_threshold,
            "check_healthy_threshold": lbaas.check_healthy_threshold,
        }
    
        forwarding_rules = []
        for rule in LBaaSForwadRule.objects.filter(lbaas=lbaas, is_deleted=False):
            forwarding_rules.append(
                {
                    "entry_port": rule.entry_port,
                    "entry_protocol": rule.entry_protocol,
                    "target_port": rule.target_port,
                    "target_protocol": rule.target_protocol,
                }
            )

        sticky_sessions = {}
        if sticky_sessions:
            sticky_sessions = {
                "cookie_ttl": lbaas.sticky_sessions_cookie_ttl,
                "cookie_name": lbaas.sticky_sessions_cookie_name,
            }

        virtances = []
        for l_v in LBaaSVirtance.objects.filter(lbaas=lbaas, is_deleted=False):
            ipv4_address = IPAddress.objects.get(
                virtance=l_v.virtance, network__type=Network.PRIVATE, is_float=False
            ).address
            virtances.append(
                {
                    "virtance_id": l_v.virtance.id,
                    "ipv4_address": ipv4_address,
                }
            )

        lbaas_vars = {
            "health": health,
            "virtances": virtances,
            "sticky_sessions": sticky_sessions,
            "forwarding_rules": forwarding_rules,
            "redirect_to_https": lbaas.redirect_http_to_https,
            "ipv4_public_address": ipv4_private_address,
            "ipv4_private_address": ipv4_private_address,
        }
        error, task = provision_lbaas(lbaas.ipv4_private_address, private_key, reload_tasks, lbaas_vars=lbaas_vars)
        if error:
            error_message = error
            if task:
                error_message = f"Task: {task}. Error: {error}"
            virtance_error(lbaas.virtance.id, error_message, event="lbaas_reload")
        else:
            lbaas.reset_events()


@app.task
def delete_lbaas(lbaas_id):
    lbaas = LBaaS.objects.get(id=lbaas_id)
    lbaas.event = LBaaS.DELETE
    lbaas.save()
    
    if delete_virtance(lbaas.virtance.id):
        lbaas.reset_events()
        lbaas.delete()
