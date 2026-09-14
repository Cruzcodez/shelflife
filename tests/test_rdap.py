"""The domain checker, against recorded RDAP responses. No network."""

import unittest
import urllib.error
from datetime import date
from pathlib import Path

from shelflife.checkers.rdap import RDAP_BASE, expiration_from, rdap_expiry
from shelflife.models import Item

FIXTURES = Path(__file__).parent / "fixtures"


def domain_item(domain: str) -> Item:
    return Item(name=domain, type="domain", owner="o", expires=None, check={"domain": domain})


def canned(status: int, body: str):
    calls = []

    def fetch(url, timeout):
        calls.append(url)
        return status, body

    fetch.calls = calls
    return fetch


class ReadsRealResponse(unittest.TestCase):
    def test_example_com(self):
        fetch = canned(200, (FIXTURES / "rdap-example.com.json").read_text())
        self.assertEqual(rdap_expiry(domain_item("example.com"), fetch), date(2027, 8, 13))
        self.assertEqual(fetch.calls, [RDAP_BASE + "example.com"])

    def test_domain_is_normalized_before_lookup(self):
        fetch = canned(200, (FIXTURES / "rdap-example.com.json").read_text())
        rdap_expiry(domain_item("  Example.COM. "), fetch)
        self.assertEqual(fetch.calls, [RDAP_BASE + "example.com"])


class ExplainsFailures(unittest.TestCase):
    def assertFails(self, fetch, domain: str, fragment: str):
        with self.assertRaises(RuntimeError) as ctx:
            rdap_expiry(domain_item(domain), fetch)
        self.assertIn(fragment, str(ctx.exception))

    def test_tld_without_rdap_says_use_a_manual_date(self):
        fetch = canned(404, (FIXTURES / "rdap-no-service.json").read_text())
        self.assertFails(fetch, "example.de", ".de has no RDAP service")

    def test_unregistered_domain(self):
        self.assertFails(canned(404, ""), "nonexistent-zz9q.com", "not registered")

    def test_other_http_status(self):
        self.assertFails(canned(503, "busy"), "example.com", "HTTP 503")

    def test_body_that_is_not_json(self):
        self.assertFails(canned(200, "<html>"), "example.com", "not JSON")

    def test_no_expiration_event(self):
        body = '{"objectClassName": "domain", "events": [{"eventAction": "registration"}]}'
        self.assertFails(canned(200, body), "example.com", "no expiration event")

    def test_network_failure(self):
        def fetch(url, timeout):
            raise urllib.error.URLError("connection refused")

        self.assertFails(fetch, "example.com", "lookup for example.com failed")

    def test_timeout(self):
        def fetch(url, timeout):
            raise TimeoutError()

        self.assertFails(fetch, "example.com", "did not answer within")

    def test_json_that_is_not_an_object(self):
        self.assertFails(canned(200, "[1, 2, 3]"), "example.com", "not a domain object")

    def test_unreadable_date(self):
        payload = {"events": [{"eventAction": "expiration", "eventDate": "someday"}]}
        with self.assertRaises(RuntimeError) as ctx:
            expiration_from(payload, "example.com")
        self.assertIn("unreadable", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
