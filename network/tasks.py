from webvirtcloud.celery import app


@app.task
def get_free_ipv4_public():
    pass


def get_free_ipv4_compute():
    pass


def get_free_ipv4_private():
    pass


def get_free_ipv6_public():
    pass
