#!/usr/bin/python3

import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from upclink_security import safe_vpn_error, sanitize


BUS_NAME = "org.upclink.VPN"
OBJECT_PATH = "/org/upclink/VPN"
INTERFACE = "org.upclink.VPN"

POLKIT_ACTION = "org.upclink.vpn.manage"

VPN_HOST = "myupclink.upc.edu:443"
SAML_URL = (
    "https://myupclink.upc.edu:443/"
    "remote/saml/start?redirect=1"
)

PPP_INTERFACE = "upclink0"

OPENFORTIVPN = "/usr/bin/openfortivpn"
PKCHECK = "/usr/bin/pkcheck"
NMCLI = "/usr/bin/nmcli"

SAML_CALLBACK_PORT = 8020


class NotAuthorized(dbus.DBusException):
    _dbus_error_name = "org.upclink.VPN.Error.NotAuthorized"


class OperationFailed(dbus.DBusException):
    _dbus_error_name = "org.upclink.VPN.Error.OperationFailed"


class UpclinkVPNService(dbus.service.Object):

    def __init__(self, bus):
        self.bus_name = dbus.service.BusName(
            BUS_NAME,
            bus=bus,
            do_not_queue=True,
        )

        super().__init__(
            self.bus_name,
            OBJECT_PATH,
        )

        self.process = None
        self.state = "disconnected"
        self.message = ""
        self.connected_since = 0
        self.last_error = ""
        self.disconnect_requested = False
        self.tunnel_lost = False

        GLib.timeout_add_seconds(
            1,
            self.poll_process,
        )

    @dbus.service.signal(
        INTERFACE,
        signature="ssx",
    )
    def StateChanged(
        self,
        state,
        message,
        connected_since,
    ):
        pass

    def set_state(
        self,
        state,
        message="",
        connected_since=None,
    ):
        message = sanitize(message)

        changed = (
            state != self.state
            or message != self.message
        )

        self.state = state
        self.message = message

        if connected_since is not None:
            self.connected_since = connected_since
        elif state != "connected":
            self.connected_since = 0

        if changed:
            self.StateChanged(
                self.state,
                self.message,
                self.connected_since,
            )

    def authorize(self, sender):
        if not sender:
            raise NotAuthorized(
                "No se pudo identificar al solicitante."
            )

        try:
            result = subprocess.run(
                [
                    PKCHECK,
                    "--action-id",
                    POLKIT_ACTION,
                    "--system-bus-name",
                    sender,
                    "--allow-user-interaction",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=120,
            )

        except subprocess.TimeoutExpired as error:
            raise NotAuthorized(
                "La autorización ha caducado."
            ) from error

        if result.returncode != 0:
            if result.stderr:
                print(
                    sanitize(result.stderr),
                    file=sys.stderr,
                )

            raise NotAuthorized("Autorización denegada.")

    def process_running(self):
        return (
            self.process is not None
            and self.process.poll() is None
        )

    @staticmethod
    def interface_present():
        return Path(
            "/sys/class/net",
            PPP_INTERFACE,
        ).exists()

    @staticmethod
    def saml_port_available():
        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as probe:
            try:
                probe.bind(("127.0.0.1", SAML_CALLBACK_PORT))
            except OSError:
                return False

        return True

    @staticmethod
    def refresh_dns():
        if not Path(NMCLI).is_file():
            return

        try:
            subprocess.run(
                [
                    NMCLI,
                    "--wait",
                    "5",
                    "general",
                    "reload",
                    "dns-rc",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=10,
            )

        except (OSError, subprocess.TimeoutExpired):
            pass

    def read_output(self, process):
        if process.stdout is None:
            return

        for line in process.stdout:
            GLib.idle_add(
                self.handle_output,
                process,
                line,
            )

    def wait_process(self, process):
        return_code = process.wait()

        GLib.idle_add(
            self.process_finished,
            process,
            return_code,
        )

    def handle_output(
        self,
        process,
        raw_line,
    ):
        if process is not self.process:
            return GLib.SOURCE_REMOVE

        line = sanitize(raw_line)
        lower = line.lower()

        if "authenticated." in lower:
            self.set_state(
                "connecting",
                "Autenticación completada. "
                "Creando el túnel…",
            )

        if (
            f"interface {PPP_INTERFACE} is up"
            in lower
            or "tunnel is up and running"
            in lower
        ):
            started = (
                self.connected_since
                or int(time.time())
            )

            self.set_state(
                "connected",
                "",
                started,
            )

        if any(
            marker in lower
            for marker in ("error:", "failed", "failure")
        ):
            self.last_error = safe_vpn_error(line)

        return GLib.SOURCE_REMOVE

    def process_finished(
        self,
        process,
        return_code,
    ):
        if process is not self.process:
            return GLib.SOURCE_REMOVE

        self.refresh_dns()

        tunnel_lost = self.tunnel_lost
        requested = self.disconnect_requested
        last_error = self.last_error

        self.process = None
        self.tunnel_lost = False
        self.disconnect_requested = False
        self.last_error = ""

        if tunnel_lost:
            self.set_state(
                "error",
                last_error or "Se ha perdido el túnel VPN.",
            )

        elif requested:
            self.set_state("disconnected")

        elif return_code == 0:
            self.set_state(
                "disconnected",
                "La conexión ha finalizado.",
            )

        else:
            message = (
                last_error
                or (
                    "openfortivpn terminó con "
                    f"el código {return_code}."
                )
            )

            self.set_state(
                "error",
                message,
            )

        return GLib.SOURCE_REMOVE

    def poll_process(self):
        if not self.process_running():
            return GLib.SOURCE_CONTINUE

        if self.interface_present():
            started = (
                self.connected_since
                or int(time.time())
            )

            self.set_state(
                "connected",
                "",
                started,
            )

        elif self.state == "connected":
            self.tunnel_lost = True
            self.last_error = "Se ha perdido el túnel VPN."

            self.set_state(
                "error",
                self.last_error,
            )

            try:
                os.killpg(
                    self.process.pid,
                    signal.SIGINT,
                )

            except ProcessLookupError:
                pass

        return GLib.SOURCE_CONTINUE

    @dbus.service.method(
        INTERFACE,
        in_signature="",
        out_signature="a{sv}",
    )
    def GetStatus(self):
        if self.process_running():
            pid = self.process.pid
        else:
            pid = 0

        return dbus.Dictionary(
            {
                "state": dbus.String(
                    self.state
                ),
                "message": dbus.String(
                    self.message
                ),
                "authentication_url": dbus.String(
                    SAML_URL
                ),
                "connected_since": dbus.Int64(
                    self.connected_since
                ),
                "pid": dbus.UInt32(pid),
            },
            signature="sv",
        )

    @dbus.service.method(
        INTERFACE,
        in_signature="",
        out_signature="s",
    )
    def GetAuthenticationUrl(self):
        return SAML_URL

    @dbus.service.method(
        INTERFACE,
        in_signature="",
        out_signature="s",
        sender_keyword="sender",
    )
    def Connect(self, sender=None):
        self.authorize(sender)

        if self.process_running():
            return "already-running"

        if self.interface_present():
            raise OperationFailed(
                f"La interfaz {PPP_INTERFACE} "
                "ya está en uso."
            )

        if not self.saml_port_available():
            raise OperationFailed(
                "El puerto local de autenticación SAML "
                f"({SAML_CALLBACK_PORT}) está en uso. "
                "Ciérralo antes de conectar."
            )

        command = [
            OPENFORTIVPN,
            VPN_HOST,
            f"--saml-login={SAML_CALLBACK_PORT}",
            f"--pppd-ifname={PPP_INTERFACE}",
        ]

        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                start_new_session=True,
                close_fds=True,
            )

        except OSError as error:
            self.process = None

            print(str(error), file=sys.stderr)

            self.set_state(
                "error",
                "No se pudo iniciar el proceso VPN.",
            )

            raise OperationFailed(
                "No se pudo iniciar el proceso VPN."
            ) from error

        self.disconnect_requested = False
        self.last_error = ""
        self.connected_since = 0

        self.set_state(
            "authenticating",
            "Abre la autenticación UPC "
            "en el navegador.",
        )

        threading.Thread(
            target=self.read_output,
            args=(self.process,),
            daemon=True,
        ).start()

        threading.Thread(
            target=self.wait_process,
            args=(self.process,),
            daemon=True,
        ).start()

        return "authentication-required"

    @dbus.service.method(
        INTERFACE,
        in_signature="",
        out_signature="s",
        sender_keyword="sender",
    )
    def Disconnect(self, sender=None):
        self.authorize(sender)

        if not self.process_running():
            self.set_state("disconnected")
            return "already-disconnected"

        self.disconnect_requested = True

        try:
            os.killpg(
                self.process.pid,
                signal.SIGINT,
            )

        except ProcessLookupError:
            self.set_state("disconnected")

        return "disconnect-requested"


def main():
    DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    try:
        service = UpclinkVPNService(bus)
    except dbus.exceptions.DBusException as error:
        print(
            "No se pudo registrar el servicio UPClink VPN "
            f"en D-Bus: {error}",
            file=sys.stderr,
        )
        sys.exit(1)

    loop = GLib.MainLoop()

    # Mantener viva la referencia del servicio.
    service

    loop.run()


if __name__ == "__main__":
    main()
