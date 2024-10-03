import importlib


def reload_lbaas_helper(lbaas_id):
    lbaas_tasks = importlib.import_module('lbaas.tasks')
    lbaas_tasks.reload_lbaas(lbaas_id)
