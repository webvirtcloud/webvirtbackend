from django.conf import settings
from webvirtcloud.celery import app

from .models import DBaaS
from network.models import Network, IPAddress
from virtance.tasks import create_virtance
from virtance.provision import ansible_play
from virtance.utils import check_ssh_connect, decrypt_data, virtance_error


provision_tasks = [
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
                "src": "ansible/dbaas/resolv.conf.j2",
                "dest": "/etc/resolv.conf",
                "owner": "root",
                "group": "root",
                "mode": "0644",
            },
        },
    },
    {
        "name": "Update apt cache",
        "action": {
            "module": "shell",
            "args": "apt-get update -y --allow-releaseinfo-change",
        },
    },
    {
        "name": "Install package dependencies",
        "action": {
            "module": "apt",
            "args": {
                "pkg": [
                    "   ",
                    "prometheus-node-exporter",
                    "prometheus-postgres-exporter",
                    "python3-psycopg2",
                    "postgresql-common",
                    "iptables-persistent",
                ],
                "state": "latest",
                "update_cache": True,
            },
        },
    },
    {
        "name": "Add PostgreSQL apt repository",
        "action": {
            "module": "shell",
            "args": "echo '\n' | /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh",
            "warn": False,
        },
    },
    {
        "name": "Install PostgreSQL server package",
        "action": {
            "module": "apt",
            "args": {
                "pkg": "postgresql-{{ version }}",
                "state": "latest",
                "update_cache": True,
            },
        },
    },
    {
        "name": "Allow PostgreSQL list on all interfaces",
        "action": {
            "module": "replace",
            "args": {
                "dest": "/etc/postgresql/{{ version }}/main/postgresql.conf",
                "regexp": "#listen_addresses = 'localhost'",
                "replace": "listen_addresses = '*'",
            },
        },
    },
    {
        "name": "Allow PostgreSQL connections from all hosts",
        "action": {
            "module": "lineinfile",
            "args": {
                "path": "/etc/postgresql/{{ version }}/main/pg_hba.conf",
                "line": "host    all             all             0.0.0.0/0               md5",
            },
        },
    },
    {
        "name": "Create PostgreSQL master user",
        "action": {"module": "user", "args": {"name": "{{ account.master.name }}", "shell": "/bin/bash"}},
    },
    {
        "name": "Create PostgreSQL dbadmin user",
        "action": {
            "module": "postgresql_user",
            "args": {
                "user": "{{ account.admin.name }}",
                "password": "{{ account.admin.password }}",
                "role_attr_flags": "NOSUPERUSER,CREATEROLE,CREATEDB,INHERIT,BYPASSRLS",
            },
        },
        "become": True,
        "become_method": "sudo",
        "become_user": "postgres",
    },
    {
        "name": "Update master user role name",
        "action": {
            "module": "shell",
            "args": r'psql -c "UPDATE pg_authid SET rolname \= \'{{ account.master.name }}\' '
            r'WHERE rolname \= \'postgres\'"',
        },
        "become": True,
        "become_method": "sudo",
        "become_user": "postgres",
    },
    {
        "name": "Update master user password",
        "action": {
            "module": "shell",
            "args": 'psql -d postgres -c "ALTER USER {{ account.master.name }} '
            "PASSWORD '{{ account.master.password }}'\"",
        },
        "become": True,
        "become_method": "sudo",
        "become_user": "{{ account.master.name }}",
    },
    {
        "name": "Update postgres database owner to dbadmin user",
        "action": {
            "module": "shell",
            "args": 'psql -d postgres -c "ALTER DATABASE postgres OWNER TO {{ account.admin.name }}"',
        },
        "become": True,
        "become_method": "sudo",
        "become_user": "{{ account.master.name }}",
    },
    {
        "name": "Create PostgreSQL master databases",
        "action": {
            "module": "shell",
            "args": 'psql -d postgres -c "CREATE DATABASE {{ account.master.name }} OWNER {{ account.master.name }}"',
        },
        "become": True,
        "become_method": "sudo",
        "become_user": "{{ account.master.name }}",
    },
    {
        "name": "Create PostgreSQL dbadmin databases",
        "action": {
            "module": "shell",
            "args": 'psql -d postgres -c "CREATE DATABASE {{ account.admin.name }} OWNER {{ account.admin.name }}"',
        },
        "become": True,
        "become_method": "sudo",
        "become_user": "{{ account.master.name }}",
    },
    {
        "name": "Restart PostgreSQL service",
        "action": {
            "module": "systemd",
            "args": {"name": "postgresql", "state": "restarted"},
        },
    },
    {
        "name": "Configure prometheus node exporter",
        "action": {
            "module": "template",
            "args": {
                "src": "ansible/dbaas/postgres-queries.yaml.j2",
                "dest": "/etc/prometheus/postgres-queries.yaml",
                "owner": "root",
                "group": "root",
                "mode": "0644",
            },
        },
    },
    {
        "name": "Configure prometheus postgres exporter data source name",
        "action": {
            "module": "lineinfile",
            "args": {
                "path": "/etc/default/prometheus-postgres-exporter",
                "regexp": "^DATA_SOURCE_NAME=",
                "line": 'DATA_SOURCE_NAME="postgresql://{{ account.master.name }}:{{ account.master.password }}@'
                'localhost:5432/postgres?sslmode=disable"',
            },
        },
    },
    {
        "name": "Configure prometheus postgres exporter args",
        "action": {
            "module": "lineinfile",
            "args": {
                "path": "/etc/default/prometheus-postgres-exporter",
                "regexp": "^ARGS=",
                "line": 'ARGS="--extend.query-path=/etc/prometheus/postgres-queries.yaml"',
            },
        },
    },
    {
        "name": "Restart prometheus postgres exporter service",
        "action": {
            "module": "systemd",
            "args": {"name": "prometheus-postgres-exporter", "state": "restarted", "enabled": "yes"},
        },
    },
    {
        "name": "Add prometheus postgres exporter to prometheus config",
        "action": {
            "module": "blockinfile",
            "args": {
                "path": "/etc/prometheus/prometheus.yml",
                "block": "  - job_name: postgres\n    static_configs:\n      - targets: ['localhost:9187']",
                "marker": "# {mark} ANSIBLE MANAGED BLOCK - PostgreSQL Exporter",
            },
        },
    },
    {
        "name": "Restart prometheus service",
        "action": {
            "module": "systemd",
            "args": {"name": "prometheus", "state": "restarted", "enabled": "yes"},
        },
    },
    {
        "name": "Create iptables rules",
        "action": {
            "module": "template",
            "args": {
                "src": "ansible/dbaas/rules.v4.j2",
                "dest": "/etc/iptables/rules.v4",
                "owner": "root",
                "group": "root",
                "mode": "0644",
            },
        },
    },
    {
        "name": "Restart iptables service",
        "action": {"module": "systemd", "args": {"name": "netfilter-persistent", "state": "restarted"}},
    },
    {
        "name": "Configure sshd to listen on private network",
        "action": {
            "module": "replace",
            "args": {
                "dest": "/etc/ssh/sshd_config",
                "regexp": "#ListenAddress 0.0.0.0",
                "replace": "ListenAddress {{ network.private.v4.address }}",
            },
        },
    },
    {"name": "Restart sshd service", "action": {"module": "systemd", "args": {"name": "sshd", "state": "reloaded"}}},
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
                "ipv4_public_address": ipv4_public.address,
                "ipv4_private_address": ipv4_private.address,
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
