"""Date math, ordering, exit codes, and the promise that 'source' always tells the truth."""

import json
import unittest
from datetime import date

from expiry_tracker.models import Item, Result
from expiry_tracker.report import evaluate, exit_code, render_json, render_table, sort_for_report

TODAY = date(2026, 9, 14)


def manual(name, expires, type_="license"):
    return Item(name=name, type=type_, owner="o@example.com", expires=expires)


def live(name, type_="tls"):
    check = {"host": "h", "port": 443} if type_ == "tls" else {"domain": "d"}
    return Item(name=name, type=type_, owner="o@example.com", check=check)


class StatusAndDays(unittest.TestCase):
    def test_days_left_is_signed(self):
        r = Result(
            item=manual("a", date(2026, 9, 24)), expires=date(2026, 9, 24), source="inventory"
        )
        self.assertEqual(r.days_left(TODAY), 10)
        r = Result(item=manual("b", date(2026, 9, 4)), expires=date(2026, 9, 4), source="inventory")
        self.assertEqual(r.days_left(TODAY), -10)

    def test_status_boundaries(self):
        def status(expires, threshold=30):
            r = Result(item=manual("x", expires), expires=expires, source="inventory")
            return r.status(TODAY, threshold)

        self.assertEqual(status(date(2026, 9, 13)), "expired")  # yesterday
        self.assertEqual(status(date(2026, 9, 14)), "expiring")  # today: 0 days, inside window
        self.assertEqual(status(date(2026, 10, 14)), "expiring")  # exactly 30 days: inside
        self.assertEqual(status(date(2026, 10, 15)), "ok")  # 31 days: outside
        self.assertEqual(status(date(2026, 10, 15), threshold=31), "expiring")

    def test_unchecked_and_error_statuses(self):
        u = Result(item=live("u"), expires=None, source="unchecked")
        e = Result(item=live("e"), expires=None, source="error", error="timeout")
        self.assertEqual(u.status(TODAY, 30), "unchecked")
        self.assertEqual(e.status(TODAY, 30), "error")


class Evaluate(unittest.TestCase):
    def test_manual_items_come_from_inventory(self):
        [r] = evaluate([manual("a", date(2027, 1, 1))])
        self.assertEqual(r.source, "inventory")
        self.assertEqual(r.expires, date(2027, 1, 1))

    def test_live_items_with_no_checker_are_unchecked_not_guessed(self):
        [r] = evaluate([live("t")], checkers={})
        self.assertEqual(r.source, "unchecked")
        self.assertIsNone(r.expires)

    def test_live_items_use_their_checker(self):
        [r] = evaluate([live("t")], checkers={"tls": lambda item: date(2026, 12, 1)})
        self.assertEqual(r.source, "live")
        self.assertEqual(r.expires, date(2026, 12, 1))

    def test_a_failing_checker_becomes_an_error_row_not_a_crash(self):
        def boom(item):
            raise ConnectionError("no route to host")

        good = manual("fine", date(2027, 1, 1))
        results = evaluate([live("bad"), good], checkers={"tls": boom})
        self.assertEqual(results[0].source, "error")
        self.assertIn("no route", results[0].error)
        self.assertEqual(results[1].source, "inventory")  # the run continued


class Ordering(unittest.TestCase):
    def test_errors_then_unchecked_then_soonest(self):
        rs = evaluate(
            [manual("far", date(2028, 1, 1)), manual("soon", date(2026, 9, 20)), live("unchecked")]
        )
        rs.append(Result(item=live("broken"), expires=None, source="error", error="x"))
        names = [r.item.name for r in sort_for_report(rs, TODAY)]
        self.assertEqual(names, ["broken", "unchecked", "soon", "far"])


class ExitCodes(unittest.TestCase):
    def test_zero_when_everything_is_fine(self):
        rs = evaluate([manual("a", date(2028, 1, 1))])
        self.assertEqual(exit_code(rs, TODAY, 30), 0)

    def test_one_when_anything_is_expiring_or_expired(self):
        rs = evaluate([manual("a", date(2028, 1, 1)), manual("b", date(2026, 9, 20))])
        self.assertEqual(exit_code(rs, TODAY, 30), 1)
        rs = evaluate([manual("c", date(2020, 1, 1))])
        self.assertEqual(exit_code(rs, TODAY, 30), 1)

    def test_two_when_something_could_not_be_checked(self):
        rs = evaluate([manual("a", date(2028, 1, 1)), live("t")])
        self.assertEqual(exit_code(rs, TODAY, 30), 2)

    def test_expiring_outranks_unchecked(self):
        # If something is about to expire AND something couldn't be checked, 1 wins.
        # The actionable problem is the one to surface.
        rs = evaluate([manual("a", date(2026, 9, 15)), live("t")])
        self.assertEqual(exit_code(rs, TODAY, 30), 1)

    def test_threshold_changes_the_answer(self):
        rs = evaluate([manual("a", date(2026, 9, 24))])  # 10 days out
        self.assertEqual(exit_code(rs, TODAY, 30), 1)
        self.assertEqual(exit_code(rs, TODAY, 5), 0)


class Rendering(unittest.TestCase):
    def test_table_marks_source_so_a_reader_can_tell_what_was_verified(self):
        rs = evaluate([manual("typed", date(2026, 9, 20)), live("live-thing")])
        out = render_table(rs, TODAY, 30)
        self.assertIn("inventory", out)
        self.assertIn("unchecked", out)
        self.assertIn("EXPIRING", out)
        self.assertIn("could not be checked", out)

    def test_table_shows_error_text(self):
        rs = [Result(item=live("b"), expires=None, source="error", error="connection refused")]
        self.assertIn("connection refused", render_table(rs, TODAY, 30))

    def test_json_is_machine_readable_and_complete(self):
        rs = evaluate([manual("a", date(2026, 9, 20), type_="api-key")])
        payload = json.loads(render_json(rs, TODAY, 30))
        self.assertEqual(payload["threshold_days"], 30)
        self.assertEqual(payload["today"], "2026-09-14")
        [row] = payload["items"]
        self.assertEqual(row["status"], "expiring")
        self.assertEqual(row["days_left"], 6)
        self.assertEqual(row["source"], "inventory")
        self.assertIsNone(row["error"])

    def test_empty_inventory(self):
        self.assertIn("empty", render_table([], TODAY, 30))


if __name__ == "__main__":
    unittest.main()
