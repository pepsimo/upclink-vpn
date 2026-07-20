import re


def sanitize(text):
    """Elimina cookies, tokens y parámetros SAML."""

    if text is None:
        return ""

    value = str(text).strip()

    replacements = (
        (
            (
                r"(?i)((?:SVPNCOOKIE|SAMLResponse|SAMLRequest|RelayState)"
                r"\s*[:=]\s*)\S+"
            ),
            r"\1[OCULTO]",
        ),
        (
            (
                r"(?i)([?&](?:id|token|session|code|SAMLResponse|"
                r"SAMLRequest|RelayState)=)[^&\s]+"
            ),
            r"\1[OCULTO]",
        ),
        (
            (
                r"(?i)((?:cookie|token|password|passwd|secret|session)"
                r"\s*[:=]\s*)\S+"
            ),
            r"\1[OCULTO]",
        ),
        (
            r"(?i)(Authorization\s*:\s*(?:Bearer|Basic)\s+)\S+",
            r"\1[OCULTO]",
        ),
    )

    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value)

    return value[:500]


def safe_vpn_error(text):
    """Convierte errores de openfortivpn en mensajes públicos seguros."""

    value = sanitize(text).casefold()

    categories = (
        (
            ("certificate", "certificado", "x509"),
            "No se pudo validar el certificado del servidor VPN.",
        ),
        (
            (
                "resolve",
                "name or service not known",
                "temporary failure in name resolution",
            ),
            "No se pudo localizar el servidor VPN.",
        ),
        (
            ("authentication", "login", "permission denied", "401", "403"),
            "La autenticación VPN no se ha completado.",
        ),
        (
            ("timeout", "timed out"),
            "Se agotó el tiempo de espera al conectar con la VPN.",
        ),
        (
            ("refused", "unreachable", "network is down"),
            "No se pudo establecer la comunicación con el servidor VPN.",
        ),
    )

    for markers, message in categories:
        if any(marker in value for marker in markers):
            return message

    return "No se pudo establecer la conexión VPN."
