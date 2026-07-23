#!/usr/bin/python3

import importlib.util
import socket
import sys
import unittest
from pathlib import Path
from unittest import mock


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
SERVICE_PATH = BACKEND_DIR / "upclink_vpn_service.py"

sys.path.insert(0, str(BACKEND_DIR))

SPEC = importlib.util.spec_from_file_location(
    "upclink_vpn_service_test",
    SERVICE_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("No se pudo cargar el backend para las pruebas.")

SERVICE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SERVICE)


class FakeProcess:
    """Simula un proceso vivo sin lanzar openfortivpn de verdad."""

    def poll(self):
        return None


def make_service(state="disconnected", process=None):
    service = object.__new__(SERVICE.UpclinkVPNService)
    service.process = process
    service.state = state
    service.message = ""
    service.connected_since = 0
    service.last_error = ""
    service.disconnect_requested = False
    service.StateChanged = lambda *args, **kwargs: None
    return service


class PollProcessTests(unittest.TestCase):

    def test_stale_connected_state_is_demoted_when_interface_disappears(self):
        service = make_service(
            state="connected",
            process=FakeProcess(),
        )
        service.connected_since = 100

        with mock.patch.object(
            SERVICE.UpclinkVPNService,
            "interface_present",
            return_value=False,
        ):
            service.poll_process()

        self.assertEqual(service.state, "error")

    def test_connected_state_is_kept_while_interface_is_present(self):
        service = make_service(
            state="connected",
            process=FakeProcess(),
        )
        service.connected_since = 100

        with mock.patch.object(
            SERVICE.UpclinkVPNService,
            "interface_present",
            return_value=True,
        ):
            service.poll_process()

        self.assertEqual(service.state, "connected")

    def test_no_state_change_while_process_is_not_running(self):
        service = make_service(state="authenticating", process=None)

        service.poll_process()

        self.assertEqual(service.state, "authenticating")


class SamlPortTests(unittest.TestCase):

    def test_port_reported_busy_is_not_available(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blocker:
            blocker.bind(("127.0.0.1", 0))
            port = blocker.getsockname()[1]
            blocker.listen(1)

            with mock.patch.object(
                SERVICE,
                "SAML_CALLBACK_PORT",
                port,
            ):
                self.assertFalse(
                    SERVICE.UpclinkVPNService.saml_port_available()
                )

    def test_connect_refuses_when_saml_port_is_taken(self):
        service = make_service(state="disconnected", process=None)

        with mock.patch.object(
            SERVICE.UpclinkVPNService,
            "authorize",
        ), mock.patch.object(
            SERVICE.UpclinkVPNService,
            "interface_present",
            return_value=False,
        ), mock.patch.object(
            SERVICE.UpclinkVPNService,
            "saml_port_available",
            return_value=False,
        ):
            with self.assertRaises(SERVICE.OperationFailed):
                service.Connect(sender=":1.1")


class AuthorizeTests(unittest.TestCase):

    def test_denied_authorization_does_not_leak_subprocess_stderr(self):
        service = make_service()
        secret = "SVPNCOOKIE=dato-muy-secreto"

        fake_result = mock.Mock(returncode=1, stderr=secret)

        with mock.patch.object(
            SERVICE.subprocess,
            "run",
            return_value=fake_result,
        ):
            with self.assertRaises(SERVICE.NotAuthorized) as context:
                service.authorize(":1.1")

        self.assertNotIn("dato-muy-secreto", str(context.exception))


if __name__ == "__main__":
    unittest.main()
