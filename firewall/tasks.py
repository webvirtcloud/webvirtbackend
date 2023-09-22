from webvirtcloud.celery import app
from .models import Firewall


@app.task
def firewall_attach(firewall_id, virtance_id):
    pass
