from django.conf import settings

from network.models import IPAddress, Network
from virtance.provision import ansible_play
from virtance.tasks import create_virtance, delete_virtance
from virtance.utils import check_ssh_connect, decrypt_data, virtance_error
from webvirtcloud.celery import app

from .models import DBaaS

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
        "name": "Create resolv.conf file with custom DNS servers",
        "action": {
            "module": "copy",
            "args": {
                "dest": "/etc/resolv.conf",
                "content": "nameserver 1.1.1.1\nnameserver 8.8.8.8\n",
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
        "action": {"module": "user", "args": {"name": "{{ master_login }}", "shell": "/bin/bash"}},
    },
    {
        "name": "Create PostgreSQL dbadmin user",
        "action": {
            "module": "postgresql_user",
            "args": {
                "user": "{{ admin_login }}",
                "password": "{{ admin_password }}",
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
            "args": r'psql -c "UPDATE pg_authid SET rolname \= \'{{ master_login }}\' WHERE rolname \= \'postgres\'"',
        },
        "become": True,
        "become_method": "sudo",
        "become_user": "postgres",
    },
    {
        "name": "Update master user password",
        "action": {
            "module": "shell",
            "args": "psql -d postgres -c \"ALTER USER {{ master_login }} WITH PASSWORD '{{ master_password }}'\"",
        },
        "become": True,
        "become_method": "sudo",
        "become_user": "{{ master_login }}",
    },
    {
        "name": "Update postgres database owner to dbadmin user",
        "action": {
            "module": "shell",
            "args": 'psql -d postgres -c "ALTER DATABASE postgres OWNER TO {{ admin_login }}"',
        },
        "become": True,
        "become_method": "sudo",
        "become_user": "{{ master_login }}",
    },
    {
        "name": "Create default database",
        "action": {
            "module": "shell",
            "args": 'psql -d postgres -c "CREATE DATABASE {{ default_db_name }} OWNER {{ admin_login }}"',
        },
        "become": True,
        "become_method": "sudo",
        "become_user": "{{ master_login }}",
    },
    {
        "name": "Restart PostgreSQL service",
        "action": {
            "module": "systemd",
            "args": {"name": "postgresql", "state": "restarted"},
        },
    },
    {
        "name": "Configure prometheus postgres exporter data source name",
        "action": {
            "module": "lineinfile",
            "args": {
                "path": "/etc/default/prometheus-postgres-exporter",
                "regexp": "^DATA_SOURCE_NAME=",
                "line": 'DATA_SOURCE_NAME="postgresql://{{ master_login }}:{{ master_password }}@'
                'localhost:5432/postgres?sslmode=disable"',
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
                "replace": "ListenAddress {{ ipv4_private_address }}",
            },
        },
    },
    {"name": "Restart sshd service", "action": {"module": "systemd", "args": {"name": "sshd", "state": "reloaded"}}},
]


update_admin_password_tasks = [
    {
        "name": "Update admin user password",
        "action": {
            "module": "shell",
            "args": "psql -d postgres -c \"ALTER USER {{ admin_login }} WITH PASSWORD '{{ admin_password }}'\"",
        },
        "become": True,
        "become_method": "sudo",
        "become_user": "{{ master_login }}",
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
                "version": dbaas.dbms.version,
                "admin_login": settings.DBAAS_ADMIN_LOGIN,
                "admin_password": decrypt_data(dbaas.admin_secret),
                "master_login": settings.DBAAS_MASTER_LOGIN,
                "master_password": decrypt_data(dbaas.master_secret),
                "default_db_name": settings.DBAAS_DEFAULT_DB_NAME,
                "ipv4_public_address": ipv4_public.address,
                "ipv4_private_address": ipv4_private.address,
                "ipv4_private_gateway": ipv4_private.network.gateway,
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


@app.task
def update_admin_password_dbaas(dbaas_id):
    dbaas = DBaaS.objects.get(id=dbaas_id)
    private_key = decrypt_data(dbaas.private_key)
    ipv4_private = IPAddress.objects.get(virtance=dbaas.virtance, network__type=Network.PRIVATE, is_float=False)

    if check_ssh_connect(ipv4_private.address, private_key=private_key):
        dbaas_vars = {
            "admin_login": settings.DBAAS_ADMIN_LOGIN,
            "admin_password": decrypt_data(dbaas.admin_secret),
            "master_login": settings.DBAAS_MASTER_LOGIN,
        }
        error, task = provision_dbaas(
            ipv4_private.address, private_key, update_admin_password_tasks, dbaas_vars=dbaas_vars
        )
        if error:
            error_message = error
            if task:
                error_message = f"Task: {task}. Error: {error}"
            virtance_error(dbaas.virtance.id, error_message, event="update_admin_password")
        else:
            dbaas.reset_event()


@app.task
def delete_lbaas(dbaas_id):
    dbaas = DBaaS.objects.get(id=dbaas_id)

    if delete_virtance(dbaas.virtance.id):
        dbaas.reset_event()
        dbaas.delete()
