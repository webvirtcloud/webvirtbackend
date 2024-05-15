import os
import shutil
import importlib
import ansible.constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager
from ansible import context


# Create a callback plugin so we can return as a result
class ResultsCollectorCallback(CallbackBase):
    def __init__(self, *args, **kwargs):
        super(ResultsCollectorCallback, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result

    def v2_runner_on_unreachable(self, result, *args, **kwargs):
        self.host_unreachable[result._host.get_name()] = result


def ansible_play(user="root", password=None, private_key=None, port=22, hosts=[], tasks={}, extra_vars=None):
    # Update TMPDIR for ansible
    importlib.reload(C)

    # Create a temporary file for the private key
    key_file_path = None
    if private_key:
        key_file_path = os.path.join(C.DEFAULT_LOCAL_TMP , "tmp-id-rsa-priv.pem")
        with open(key_file_path, "w") as key_file:
            key_file.write(private_key)
        os.chmod(key_file_path, 0o600)

    # Set the default connection type to 'smart'
    context.CLIARGS = ImmutableDict(
        connection="smart",
        module_path=[],
        forks=10,
        become=None,
        become_method=None,
        become_user=None,
        remote_user=user,
        private_key_file=key_file_path,
        check=False,
        diff=False,
        verbosity=0,
    )

    if isinstance(hosts, str):
        hosts = hosts.split(",")
    sources = ",".join(hosts)
    if len(hosts) == 1:
        sources += ","

    # initialize
    loader = DataLoader()
    passwords = {"conn_pass": password}
    inventory = InventoryManager(loader=loader, sources=sources)
    variable_manager = VariableManager(loader=loader, inventory=inventory)

    if extra_vars:
        variable_manager._extra_vars = extra_vars

    results_callback = ResultsCollectorCallback()
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords=passwords,
        stdout_callback=results_callback,
    )

    play_source = dict(name="Ansible Play", hosts=hosts, port=port, gather_facts="no", tasks=tasks)
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    if hosts:
        try:
            tqm.run(play) 
        finally:
            tqm.cleanup()
            if loader:
                loader.cleanup_all_tmp_files()

    # Remove ansible tmpdir
    shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

    return results_callback
