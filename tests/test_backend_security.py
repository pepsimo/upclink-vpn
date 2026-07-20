#!/usr/bin/python3

import importlib.util
import unittest
from pathlib import Path


SECURITY_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "upclink_security.py"
)

SPEC = importlib.util.spec_from_file_location(
    "upclink_security_test",
    SECURITY_PATH,
)

if SPEC is None or SPEC.loader is None:
    raise RuntimeError("No se pudo cargar el backend para las pruebas.")

SECURITY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SECURITY)


class SanitizationTests(unittest.TestCase):

    def test_sensitive_values_are_hidden(self):
        cases = {
            "SVPNCOOKIE=secreto": "SVPNCOOKIE=[OCULTO]",
            "SAMLResponse: respuesta": "SAMLResponse: [OCULTO]",
            "SAMLRequest=peticion": "SAMLRequest=[OCULTO]",
            "RelayState=estado": "RelayState=[OCULTO]",
            "password: clave": "password: [OCULTO]",
            "passwd=clave": "passwd=[OCULTO]",
            "secret=valor": "secret=[OCULTO]",
            "session=abc123": "session=[OCULTO]",
            (
                "Authorization: Bearer abc.def"
            ): "Authorization: Bearer [OCULTO]",
            (
                "https://vpn/?code=abc&ok=1"
            ): "https://vpn/?code=[OCULTO]&ok=1",
        }

        for original, expected in cases.items():
            with self.subTest(original=original):
                self.assertEqual(SECURITY.sanitize(original), expected)

    def test_none_becomes_empty_text(self):
        self.assertEqual(SECURITY.sanitize(None), "")

    def test_public_messages_have_a_maximum_length(self):
        self.assertEqual(len(SECURITY.sanitize("x" * 800)), 500)

    def test_vpn_errors_do_not_expose_original_secrets(self):
        secret = "dato-muy-secreto"
        message = SECURITY.safe_vpn_error(
            f"ERROR: SVPNCOOKIE={secret}"
        )

        self.assertNotIn(secret, message)
        self.assertEqual(
            message,
            "No se pudo establecer la conexión VPN.",
        )

    def test_certificate_errors_are_classified(self):
        self.assertEqual(
            SECURITY.safe_vpn_error(
                "ERROR: certificate validation failed"
            ),
            "No se pudo validar el certificado del servidor VPN.",
        )


if __name__ == "__main__":
    unittest.main()
