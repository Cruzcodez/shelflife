"""TLS checker: connect, complete the handshake, read the certificate's expiry date.

No chain verification, on purpose. Verification fails on an expired certificate, and an expired
certificate is the exact thing this tool exists to report. Nothing is sent over the connection
after the handshake, so there is nothing for a bad certificate to protect. Reasoning recorded in
docs/decisions/0003-tls-checker-does-not-verify.md.
"""

from __future__ import annotations

import socket
import ssl
from collections.abc import Callable
from datetime import date

from ..models import Item
from ..x509 import not_after

DEFAULT_TIMEOUT = 10.0

# Seam for tests: something that returns the DER bytes of the certificate host:port presents.
FetchCert = Callable[[str, int, float], bytes]


def fetch_certificate(host: str, port: int, timeout: float = DEFAULT_TIMEOUT) -> bytes:
    """Do a real TLS handshake with host:port and return the leaf certificate as DER bytes."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with (
        socket.create_connection((host, port), timeout=timeout) as raw,
        context.wrap_socket(raw, server_hostname=host) as tls,
    ):
        der = tls.getpeercert(binary_form=True)
    if not der:
        raise RuntimeError(f"{host}:{port} completed a handshake but presented no certificate")
    return der


def tls_expiry(item: Item, fetch: FetchCert = fetch_certificate) -> date:
    """Checker for `type: tls` items. `item.check` carries host and port, validated by inventory."""
    host = item.check["host"]
    port = int(item.check.get("port", 443))
    try:
        der = fetch(host, port, DEFAULT_TIMEOUT)
    except socket.gaierror as e:
        raise RuntimeError(f"could not resolve {host}: {e}") from e
    except TimeoutError as e:
        raise RuntimeError(f"{host}:{port} did not answer within {DEFAULT_TIMEOUT:g}s") from e
    except (ssl.SSLError, OSError) as e:
        raise RuntimeError(f"{host}:{port}: {e}") from e
    return not_after(der)
