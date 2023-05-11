import os
import django
import logging
from http import cookies
from websockify import WebSocketProxy
from websockify import ProxyRequestHandler
from django.conf import settings
from django.core.management.base import BaseCommand


DIR_PATH = os.path.dirname(os.path.abspath(__file__))
CERT_PATH = os.path.join(DIR_PATH, "cert.pem")


def get_console_connection(uuid):
    django.setup()
    from virtance.models import Virtance
    from compute.webvirt import WebVirtCompute

    virtance = Virtance.objects.filter(uuid=uuid, is_deleted=False).first()

    if virtance is None or virtance.compute is None:
        logging.error(f"Fail to retrieve console connection info for UUID {uuid}: compute not found")
        raise

    wvcomp = WebVirtCompute(virtance.compute.token, virtance.compute.hostname)
    res = wvcomp.get_virtance_vnc(virtance.id)

    if res.get("detail") is not None:
        logging.error(f"Fail to retrieve console connection info for UUID {uuid}: {res.get('detail')}")
        raise

    port = res.get("vnc_port")
    host = virtance.compute.hostname

    return host, port


class CompatibilityMixIn(object):
    def _new_client(self, daemon, socket_factory):

        cookie = cookies.SimpleCookie()
        cookie.load(self.headers.get("cookie"))
        if "uuid" not in cookie:
            print("UUID not found\n")
            return False

        console_host, console_port = get_console_connection(cookie.get("uuid").value)

        cnx_debug_msg = "Connection Info:\n"
        cnx_debug_msg += f"       - VNC host: {console_host}\n"
        cnx_debug_msg += f"       - VNC port: {console_port}"

        # Direct access
        tsock = socket_factory(console_host, console_port, connect=True)

        if self.verbose and not daemon:
            print(cnx_debug_msg)
            print(self.traffic_legend)

        # Start proxying
        try:
            if self.verbose and not daemon:
                print(f"Connected to: {console_host}:{console_port}\n")
            self.do_proxy(tsock)
        except Exception:
            raise


class NovaProxyRequestHandler(ProxyRequestHandler, CompatibilityMixIn):
    def msg(self, *args, **kwargs):
        self.log_message(*args, **kwargs)

    def vmsg(self, *args, **kwargs):
        if self.verbose:
            self.msg(*args, **kwargs)

    def new_websocket_client(self):
        """
        Called after a new WebSocket connection has been established.
        """
        # Setup variable for compatibility
        daemon = self.server.daemon
        socket_factory = self.server.socket

        self._new_client(daemon, socket_factory)


class Command(BaseCommand):
    help = "noVNC daemon"

    def add_arguments(self, parser):
        parser.add_argument(
            "-vv",
            "--verbose",
            dest="verbose",
            action="store_true",
            help="Verbose mode",
            default=False,
        )

        parser.add_argument(
            "-H",
            "--host",
            dest="host",
            action="store",
            help="Listen host",
            default=settings.WEBSOCKET_HOST,
        )

        parser.add_argument(
            "-p",
            "--port",
            dest="port",
            action="store",
            help="Listen port",
            default=settings.WEBSOCKET_PORT,
        )

        parser.add_argument(
            "-c",
            "--cert",
            dest="cert",
            action="store",
            help="Certificate file path",
            default=settings.WEBSOCKET_CERT or CERT_PATH,
        )

    def handle(self, *args, **options):
        print("Starting noVNC daemon...\n")
        server = WebSocketProxy(
            RequestHandlerClass=NovaProxyRequestHandler,
            listen_host=options["host"],
            listen_port=options["port"],
            source_is_ipv6=False,
            verbose=options["verbose"],
            cert=options["cert"],
            key=None,
            ssl_only=False,
            daemon=False,
            record=False,
            web=False,
            traffic=False,
            target_host="ignore",
            target_port="ignore",
            wrap_mode="exit",
            wrap_cmd=None,
        )
        server.start_server()
