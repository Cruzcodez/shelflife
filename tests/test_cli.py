"""End to end through the command line, with a JSON inventory so it runs without PyYAML."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from expiry_tracker.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CheckCommand(unittest.TestCase):
    def test_reports_and_exits_one_when_something_is_expiring(self):
        code, out, _ = run("check", "-i", str(FIXTURES / "valid.json"), "--today", "2026-09-14")
        self.assertEqual(code, 1)  # "payments API key" expires 2026-10-01, inside 30 days
        self.assertIn("payments API key", out)
        self.assertIn("EXPIRED", out)  # "old contract" expired 2026-01-01
        self.assertIn("UNCHECKED", out)  # the two live items, no checkers yet

    def test_threshold_flag(self):
        code, out, _ = run(
            "check", "-i", str(FIXTURES / "valid.json"), "--today", "2026-09-14", "--days", "5"
        )
        # payments key is 17 days out: outside a 5-day window. old contract is still expired.
        self.assertEqual(code, 1)
        self.assertIn("EXPIRED", out)

    def test_json_flag(self):
        code, out, _ = run(
            "check", "-i", str(FIXTURES / "valid.json"), "--today", "2026-09-14", "--json"
        )
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("{"))
        self.assertIn('"source": "unchecked"', out)

    def test_bad_inventory_is_exit_two_with_a_message(self):
        code, out, err = run("check", "-i", "/nope/inventory.json")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("not found", err)


if __name__ == "__main__":
    unittest.main()
