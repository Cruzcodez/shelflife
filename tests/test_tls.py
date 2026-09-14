"""The TLS checker and the certificate parser.

The certificate is generated at test time with `openssl` so nothing key-shaped is committed.
"""

import os
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from shelflife.checkers.tls import fetch_certificate, tls_expiry
from shelflife.models import Item
from shelflife.x509 import CertificateError, _parse_time, not_after

OPENSSL = shutil.which("openssl")


def require_openssl():
    """Skip locally when openssl is missing. Fail in CI, because a skip there would quietly turn
    the real-handshake tests off and nobody would notice the coverage was gone."""
    if OPENSSL:
        return
    if os.environ.get("CI"):
        raise AssertionError("openssl is not on the CI runner's PATH; the TLS tests must run there")
    raise unittest.SkipTest("openssl not on PATH; cannot generate a test certificate")


def tls_item(host: str, port: int) -> Item:
    return Item(name=host, type="tls", owner="o", expires=None, check={"host": host, "port": port})


def make_certificate(directory: Path, days: int) -> tuple[Path, Path]:
    """Self-signed certificate valid for `days` days. Returns (cert PEM, key PEM)."""
    cert, key = directory / "cert.pem", directory / "key.pem"
    subprocess.run(
        [
            OPENSSL, "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", str(key), "-out", str(cert),
            "-days", str(days), "-subj", "/CN=localhost",
        ],
        check=True,
        capture_output=True,
    )  # fmt: skip
    return cert, key


class LocalTlsServer:
    """Accepts one connection at a time, completes the handshake, closes. Nothing else."""

    def __init__(self, cert: Path, key: Path):
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(str(cert), str(key))
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            try:
                with self.context.wrap_socket(conn, server_side=True):
                    pass
            except (ssl.SSLError, OSError):
                pass

    def close(self):
        self.sock.close()


class CertificateParser(unittest.TestCase):
    def setUp(self):
        require_openssl()

    def test_reads_not_after_from_openssl_output(self):
        with tempfile.TemporaryDirectory() as d:
            cert, _ = make_certificate(Path(d), days=30)
            der = ssl.PEM_cert_to_DER_cert(cert.read_text())
            expected = subprocess.run(
                [OPENSSL, "x509", "-in", str(cert), "-noout", "-enddate"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        # openssl prints e.g. "notAfter=Oct 14 01:40:58 2026 GMT"
        self.assertIn(not_after(der).strftime("%Y"), expected)
        self.assertAlmostEqual((not_after(der) - date.today()).days, 30, delta=1)

    def test_generalized_time_for_far_future(self):
        # RFC 5280: dates from 2050 on use GeneralizedTime. 20000 days is past 2080.
        with tempfile.TemporaryDirectory() as d:
            cert, _ = make_certificate(Path(d), days=20000)
            der = ssl.PEM_cert_to_DER_cert(cert.read_text())
        self.assertEqual(not_after(der), date.today() + timedelta(days=20000))


class CertificateParserRejectsJunk(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(CertificateError):
            not_after(b"")

    def test_not_a_sequence(self):
        with self.assertRaises(CertificateError):
            not_after(b"\x02\x01\x05")

    def test_truncated(self):
        with self.assertRaises(CertificateError):
            not_after(b"\x30\x82\x01\x00\x30")

    def test_length_field_that_claims_too_many_bytes(self):
        # 0x85 means "length is in the next 5 bytes". DER never needs more than 4 here.
        with self.assertRaises(CertificateError) as ctx:
            not_after(b"\x30\x85\x00\x00\x00\x00\x01")
        self.assertIn("bad length", str(ctx.exception))

    def test_indefinite_length_is_refused(self):
        # 0x80 alone is BER indefinite length, which DER forbids.
        with self.assertRaises(CertificateError) as ctx:
            not_after(b"\x30\x80")
        self.assertIn("bad length", str(ctx.exception))

    def test_wrong_tag_where_not_after_should_be(self):
        with self.assertRaises(CertificateError) as ctx:
            _parse_time(0x04, b"whatever")
        self.assertIn("unexpected time tag", str(ctx.exception))

    def test_unreadable_date_text(self):
        with self.assertRaises(CertificateError) as ctx:
            _parse_time(0x17, b"not-a-date")
        self.assertIn("unreadable notAfter", str(ctx.exception))

    def test_utc_and_generalized_time_parse(self):
        self.assertEqual(_parse_time(0x17, b"261014014058Z").date(), date(2026, 10, 14))
        self.assertEqual(_parse_time(0x18, b"20810617014112Z").date(), date(2081, 6, 17))


class RealHandshakeAgainstLocalServer(unittest.TestCase):
    def setUp(self):
        require_openssl()

    def test_reads_expiry_off_a_live_certificate(self):
        with tempfile.TemporaryDirectory() as d:
            cert, key = make_certificate(Path(d), days=10)
            server = LocalTlsServer(cert, key)
            try:
                found = tls_expiry(tls_item("127.0.0.1", server.port))
            finally:
                server.close()
        self.assertEqual(found, date.today() + timedelta(days=10))

    def test_fetch_does_not_require_a_trusted_chain(self):
        # Self-signed and CN=localhost while we connect by IP: a verifying client would refuse
        # this twice over. The checker must still get the certificate.
        with tempfile.TemporaryDirectory() as d:
            cert, key = make_certificate(Path(d), days=1)
            server = LocalTlsServer(cert, key)
            try:
                der = fetch_certificate("127.0.0.1", server.port, timeout=5)
            finally:
                server.close()
        self.assertTrue(der.startswith(b"\x30"))


class ExplainsFailures(unittest.TestCase):
    def test_refused_connection(self):
        # Bind and close so the port is real but nobody is listening.
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        with self.assertRaises(RuntimeError) as ctx:
            tls_expiry(tls_item("127.0.0.1", port))
        self.assertIn(f"127.0.0.1:{port}", str(ctx.exception))

    def assertFetchFailureBecomes(self, exc: Exception, fragment: str):
        def fetch(host, port, timeout):
            raise exc

        with self.assertRaises(RuntimeError) as ctx:
            tls_expiry(tls_item("h.example", 8443), fetch)
        self.assertIn(fragment, str(ctx.exception))

    def test_unresolvable_host(self):
        # Injected rather than a real lookup: the suite must not depend on DNS behavior.
        self.assertFetchFailureBecomes(
            socket.gaierror(-2, "Name or service not known"), "could not resolve"
        )

    def test_timeout(self):
        self.assertFetchFailureBecomes(TimeoutError(), "did not answer within")

    def test_handshake_failure(self):
        self.assertFetchFailureBecomes(ssl.SSLError(1, "handshake failure"), "h.example:8443")

    def test_empty_certificate_from_fetch(self):
        def fetch(host, port, timeout):
            return b""

        with self.assertRaises(CertificateError):
            tls_expiry(tls_item("h", 443), fetch)

    def test_handshake_that_presents_no_certificate(self):
        # A TLS server can complete a handshake without a certificate (anonymous cipher suites).
        # fetch_certificate must say so instead of handing empty bytes to the parser.
        with patch("shelflife.checkers.tls._handshake", return_value=b""):
            with self.assertRaises(RuntimeError) as ctx:
                fetch_certificate("h.example", 8443, timeout=1)
        self.assertIn("presented no certificate", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
