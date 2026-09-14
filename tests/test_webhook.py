"""The webhook: payload shape, summary line, failure handling, and the CLI wiring.

Posting goes through an injected `post` or a local HTTP server. Nothing leaves the machine.
"""

import io
import json
import threading
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

from shelflife import cli
from shelflife.models import Item, Result
from shelflife.net import RedirectError
from shelflife.webhook import WebhookError, build_payload, post_json, send, summary_line

FIXTURES = Path(__file__).parent / "fixtures"
TODAY = date(2026, 9, 14)


def manual(name, owner, expires):
    item = Item(name=name, type="license", owner=owner, expires=expires, check=None, note="")
    return Result(item=item, expires=expires, source="inventory")


def broken(name):
    item = Item(name=name, type="tls", owner="o", expires=None, check={"host": "h"}, note="")
    return Result(item=item, expires=None, source="error", error="boom")


class SummaryLine(unittest.TestCase):
    def test_all_fine(self):
        results = [manual("a", "o", date(2027, 1, 1))]
        self.assertEqual(summary_line(results, TODAY, 30), "shelflife: all 1 items fine.")

    def test_counts_and_soonest(self):
        results = [
            manual("old", "legal@example.com", date(2026, 1, 1)),
            manual("key", "pay@example.com", date(2026, 10, 1)),
            broken("cert"),
        ]
        line = summary_line(results, TODAY, 30)
        self.assertIn("1 expired", line)
        self.assertIn("1 expiring within 30 days", line)
        self.assertIn("1 could not be checked", line)
        # "old" expired first, so it is the soonest and it reads as days ago
        self.assertIn("Soonest: old (legal@example.com) 256 days ago", line)

    def test_expiring_today(self):
        line = summary_line([manual("k", "o", TODAY)], TODAY, 30)
        self.assertIn("k (o) today", line)


class Payload(unittest.TestCase):
    def test_is_the_json_report_plus_message_fields(self):
        results = [manual("key", "pay@example.com", date(2026, 10, 1))]
        payload = json.loads(build_payload(results, TODAY, 30))
        self.assertEqual(payload["text"], payload["content"])
        self.assertIn("1 expiring", payload["text"])
        self.assertEqual(payload["threshold_days"], 30)
        self.assertEqual(payload["items"][0]["name"], "key")
        self.assertEqual(payload["items"][0]["status"], "expiring")


class SendFailures(unittest.TestCase):
    URL = "https://hooks.example/services/T000/B000/secret-part"

    def assertFailsWithout(self, post, fragment: str):
        with self.assertRaises(WebhookError) as ctx:
            send(self.URL, [manual("k", "o", TODAY)], TODAY, 30, post)
        message = str(ctx.exception)
        self.assertIn(fragment, message)
        self.assertNotIn("secret-part", message)  # the URL is a credential; never echo it

    def test_non_2xx_status(self):
        self.assertFailsWithout(lambda u, b, t: 500, "HTTP 500")

    def test_http_error(self):
        def post(u, b, t):
            raise urllib.error.HTTPError(u, 403, "forbidden", {}, None)

        self.assertFailsWithout(post, "HTTP 403")

    def test_unreachable(self):
        def post(u, b, t):
            raise urllib.error.URLError("connection refused")

        self.assertFailsWithout(post, "could not be reached")

    def test_timeout(self):
        def post(u, b, t):
            raise TimeoutError()

        self.assertFailsWithout(post, "did not answer")

    def test_malformed_url_is_a_clean_error(self):
        for bad in ("", "   ", "hooks.example/services/secret-part", "http://hooks.example/x"):
            with self.subTest(url=bad), self.assertRaises(WebhookError) as ctx:
                send(bad, [manual("k", "o", TODAY)], TODAY, 30, lambda u, b, t: 200)
            self.assertIn("webhook URL", str(ctx.exception))
            self.assertNotIn("secret-part", str(ctx.exception))

    def test_file_scheme_is_refused(self):
        with self.assertRaises(WebhookError):
            send("file:///etc/hostname", [manual("k", "o", TODAY)], TODAY, 30)

    def test_unexpected_exception_does_not_leak_the_url(self):
        def post(u, b, t):
            raise ValueError(f"unknown url type: {u}")

        self.assertFailsWithout(post, "webhook post failed: ValueError")

    def test_non_integer_status_is_a_failure(self):
        self.assertFailsWithout(lambda u, b, t: None, "returned HTTP None")

    def test_success_is_silent(self):
        seen = []
        send(self.URL, [manual("k", "o", TODAY)], TODAY, 30, lambda u, b, t: seen.append(u) or 204)
        self.assertEqual(seen, [self.URL])


class Handler(BaseHTTPRequestHandler):
    received: list[dict] = []

    def log_message(self, *_):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        Handler.received.append(
            {
                "path": self.path,
                "type": self.headers.get("Content-Type"),
                "body": self.rfile.read(length),
            }
        )
        if self.path == "/ok":
            self.send_response(200)
        elif self.path == "/redirect":
            self.send_response(307)
            self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/ok")
        else:
            self.send_response(500)
        self.send_header("Content-Length", "0")
        self.end_headers()


class RealPost(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        Handler.received.clear()

    def test_posts_json_with_the_right_content_type(self):
        status = post_json(self.base + "/ok", b'{"text": "hi"}', timeout=5)
        self.assertEqual(status, 200)
        self.assertEqual(Handler.received[0]["type"], "application/json")
        self.assertEqual(Handler.received[0]["body"], b'{"text": "hi"}')

    def test_redirect_to_a_private_address_is_refused(self):
        # send() would refuse this plain-http URL before posting, so drive the transport directly
        # to prove the redirect rule holds on the POST path too.
        with self.assertRaises(RedirectError):
            post_json(self.base + "/redirect", b"{}", timeout=5)
        self.assertEqual(len(Handler.received), 1)  # nothing was posted to the redirect target

    def test_redirect_error_becomes_a_clean_webhook_error(self):
        def post(u, b, t):
            return post_json(self.base + "/redirect", b, t)

        with self.assertRaises(WebhookError) as ctx:
            send("https://hooks.example/x", [manual("k", "o", TODAY)], TODAY, 30, post)
        self.assertIn("refuses to follow", str(ctx.exception))


def run(*argv, env=None):
    out, err = io.StringIO(), io.StringIO()
    with (
        patch.dict("os.environ", env or {}, clear=False),
        redirect_stdout(out),
        redirect_stderr(err),
    ):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliWiring(unittest.TestCase):
    ARGS = ("check", "-i", str(FIXTURES / "valid.json"), "--today", "2026-09-14", "--offline")

    def test_posts_when_something_needs_attention(self):
        with patch("shelflife.cli.send") as send_mock:
            code, _, _ = run(*self.ARGS, "--webhook", "https://hooks.example/x")
        self.assertEqual(code, 1)
        send_mock.assert_called_once()
        self.assertEqual(send_mock.call_args.args[0], "https://hooks.example/x")

    def test_url_from_environment(self):
        with patch("shelflife.cli.send") as send_mock:
            run(*self.ARGS, env={"SHELFLIFE_WEBHOOK": "https://hooks.example/env"})
        self.assertEqual(send_mock.call_args.args[0], "https://hooks.example/env")

    def test_no_post_when_all_fine_unless_always(self):
        # valid.json has an expired item, so build a fine-only inventory on the fly.
        fine = FIXTURES.parent / "fixtures" / "fine.json"
        fine.write_text(
            '{"items": [{"name": "k", "type": "license", "owner": "o", "expires": "2030-01-01"}]}'
        )
        try:
            with patch("shelflife.cli.send") as send_mock:
                code, _, _ = run("check", "-i", str(fine), "--webhook", "https://hooks.example/x")
                self.assertEqual(code, 0)
                send_mock.assert_not_called()
                run(
                    "check",
                    "-i",
                    str(fine),
                    "--webhook",
                    "https://hooks.example/x",
                    "--webhook-always",
                )
                send_mock.assert_called_once()
        finally:
            fine.unlink()

    def test_flag_wins_over_environment(self):
        with patch("shelflife.cli.send") as send_mock:
            run(
                *self.ARGS,
                "--webhook",
                "https://hooks.example/flag",
                env={"SHELFLIFE_WEBHOOK": "https://hooks.example/env"},
            )
        self.assertEqual(send_mock.call_args.args[0], "https://hooks.example/flag")

    def test_failed_post_on_an_exit_two_run_stays_two(self):
        # valid.json with --offline has unchecked live items but also an expired item, so build
        # an inventory whose only trouble is an unchecked live item.
        only_live = FIXTURES.parent / "fixtures" / "live-only.json"
        only_live.write_text(
            '{"items": [{"name": "t", "type": "tls", "owner": "o", "check": {"host": "h"}}]}'
        )
        try:
            with patch("shelflife.cli.send", side_effect=WebhookError("webhook returned HTTP 500")):
                code, _, err = run(
                    "check",
                    "-i",
                    str(only_live),
                    "--offline",
                    "--webhook",
                    "https://hooks.example/x",
                )
        finally:
            only_live.unlink()
        self.assertEqual(code, 2)
        self.assertIn("error: webhook", err)

    def test_failed_post_keeps_exit_one_but_reports(self):
        with patch("shelflife.cli.send", side_effect=WebhookError("webhook returned HTTP 500")):
            code, _, err = run(*self.ARGS, "--webhook", "https://hooks.example/x")
        self.assertEqual(code, 1)
        self.assertIn("error: webhook returned HTTP 500", err)

    def test_failed_heartbeat_is_exit_two(self):
        fine = FIXTURES.parent / "fixtures" / "fine2.json"
        fine.write_text(
            '{"items": [{"name": "k", "type": "license", "owner": "o", "expires": "2030-01-01"}]}'
        )
        try:
            with patch("shelflife.cli.send", side_effect=WebhookError("webhook returned HTTP 500")):
                code, _, _ = run(
                    "check",
                    "-i",
                    str(fine),
                    "--webhook",
                    "https://hooks.example/x",
                    "--webhook-always",
                )
        finally:
            fine.unlink()
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
