"""The real HTTP path of the domain checker, against a local server. No outside network.

`tests/test_rdap.py` covers parsing with an injected fetch. This file covers the fetch itself:
request headers, the body cap, and which redirects get refused.
"""

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from expiry_tracker.checkers.rdap import (
    MAX_BODY_BYTES,
    RedirectError,
    fetch_url,
    redirect_refusal,
)


class Handler(BaseHTTPRequestHandler):
    seen_headers: list[dict] = []

    def log_message(self, *_):  # keep test output quiet
        pass

    def do_GET(self):
        Handler.seen_headers.append(dict(self.headers))
        if self.path == "/ok":
            self._send(200, b'{"events": []}')
        elif self.path == "/missing":
            self._send(404, b'{"title": "No RDAP service is available for this resource"}')
        elif self.path == "/big":
            self._send(200, b"x" * (MAX_BODY_BYTES + 1))
        elif self.path == "/to-loopback":
            self._redirect(f"http://127.0.0.1:{self.server.server_port}/ok")
        elif self.path == "/to-metadata":
            self._redirect("https://169.254.169.254/latest/meta-data/")
        elif self.path == "/to-plain-http":
            self._redirect("http://example.com/")
        else:
            self._send(404, b"")

    def _send(self, status: int, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", "application/rdap+json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, target: str):
        self.send_response(302)
        self.send_header("Location", target)
        self.send_header("Content-Length", "0")
        self.end_headers()


class LocalHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        Handler.seen_headers.clear()

    def test_sends_rdap_accept_header_and_a_user_agent(self):
        status, body = fetch_url(self.base + "/ok", timeout=5)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"events": []})
        sent = Handler.seen_headers[0]
        self.assertEqual(sent["Accept"], "application/rdap+json")
        self.assertIn("expiry-tracker", sent["User-Agent"])

    def test_error_status_returns_its_body(self):
        status, body = fetch_url(self.base + "/missing", timeout=5)
        self.assertEqual(status, 404)
        self.assertIn("No RDAP service", body)

    def test_oversized_body_is_refused(self):
        with self.assertRaises(RuntimeError) as ctx:
            fetch_url(self.base + "/big", timeout=5)
        self.assertIn("larger than", str(ctx.exception))

    def test_redirect_to_loopback_is_refused(self):
        with self.assertRaises(RedirectError) as ctx:
            fetch_url(self.base + "/to-loopback", timeout=5)
        self.assertIn("not https", str(ctx.exception))
        self.assertEqual(len(Handler.seen_headers), 1)  # the redirect target was never requested

    def test_redirect_to_metadata_endpoint_is_refused(self):
        with self.assertRaises(RedirectError) as ctx:
            fetch_url(self.base + "/to-metadata", timeout=5)
        self.assertIn("non-public", str(ctx.exception))

    def test_redirect_to_plain_http_is_refused(self):
        with self.assertRaises(RedirectError):
            fetch_url(self.base + "/to-plain-http", timeout=5)


class RedirectPolicy(unittest.TestCase):
    """The decision on its own, with DNS replaced, so no test resolves a real name."""

    def test_public_https_host_is_allowed(self):
        ok = redirect_refusal("https://rdap.verisign.com/com/v1/domain/x", lambda h: ["192.0.66.1"])
        self.assertIsNone(ok)

    def test_host_resolving_to_private_address_is_refused(self):
        why = redirect_refusal("https://internal.example/", lambda h: ["10.0.0.5"])
        self.assertIn("non-public", why)

    def test_host_with_one_private_address_among_public_is_refused(self):
        why = redirect_refusal("https://mixed.example/", lambda h: ["192.0.66.1", "172.16.0.1"])
        self.assertIn("non-public", why)

    def test_ip_literal_is_checked_without_resolving(self):
        def explode(host):
            raise AssertionError("must not resolve an IP literal")

        self.assertIn("non-public", redirect_refusal("https://127.0.0.1/", explode))
        self.assertIsNone(redirect_refusal("https://192.0.66.1/", explode))

    def test_unresolvable_host_is_refused(self):
        import socket

        def fail(host):
            raise socket.gaierror(-2, "no such name")

        self.assertIn("could not resolve", redirect_refusal("https://nope.invalid/", fail))

    def test_http_scheme_is_refused(self):
        self.assertEqual(
            redirect_refusal("http://rdap.org/", lambda h: ["192.0.66.1"]), "not https"
        )

    def test_missing_host_is_refused(self):
        self.assertEqual(redirect_refusal("https:///path", lambda h: []), "no host")


if __name__ == "__main__":
    unittest.main()
