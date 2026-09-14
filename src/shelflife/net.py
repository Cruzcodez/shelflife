"""HTTP rules shared by everything in this tool that talks to the network.

One rule, applied everywhere: a redirect is followed only if it points at HTTPS on a host whose
addresses are all public. The first request goes wherever the operator or the RDAP redirector
said; the redirect is third-party input, and following it blindly would let a bad redirect turn
this tool into a way to make requests at internal addresses (cloud metadata endpoints, private
services) from wherever it runs.
"""

from __future__ import annotations

import ipaddress
import socket
import urllib.parse
import urllib.request
from collections.abc import Callable


class RedirectError(RuntimeError):
    """A redirect pointed somewhere this tool refuses to follow."""


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follows a redirect only if it's HTTPS to a public host. See the module docstring."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        reason = redirect_refusal(newurl)
        if reason:
            raise RedirectError(f"refusing redirect to {newurl}: {reason}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


Resolver = Callable[[str], list[str]]


def _resolve(host: str) -> list[str]:
    return [info[4][0] for info in socket.getaddrinfo(host, None)]


def redirect_refusal(url: str, resolve: Resolver = _resolve) -> str | None:
    """Return why a redirect target must not be followed, or None if it's fine."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https":
        return "not https"
    host = parts.hostname
    if not host:
        return "no host"
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            addresses = [ipaddress.ip_address(a) for a in resolve(host)]
        except (socket.gaierror, ValueError) as e:
            return f"could not resolve {host}: {e}"
    for address in addresses:
        if not address.is_global:
            return f"{host} resolves to a non-public address ({address})"
    return None


def safe_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(SafeRedirectHandler)
