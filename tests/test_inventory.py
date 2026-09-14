"""The loader's job is to refuse anything that would leave something untracked.

Written unittest-style so it runs with `python -m unittest` and with `pytest` alike.
"""

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from shelflife.inventory import InventoryError, _parse_date, load

FIXTURES = Path(__file__).parent / "fixtures"

try:
    import yaml  # noqa: F401

    HAVE_YAML = True
except ImportError:  # pragma: no cover - only true in a sandbox without the dependency
    HAVE_YAML = False


def write_text(text: str, suffix: str) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(text)
    f.close()
    return Path(f.name)


def write_json(payload: dict) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(payload, f)
    f.close()
    return Path(f.name)


def one_item(**overrides) -> Path:
    base = {"name": "thing", "type": "license", "owner": "me@example.com", "expires": "2027-01-01"}
    base.update(overrides)
    return write_json({"items": [base]})


class LoadsValidInventory(unittest.TestCase):
    def test_reads_every_item(self):
        items = load(FIXTURES / "valid.json")
        self.assertEqual(
            [i.name for i in items],
            [
                "web TLS",
                "example.com registration",
                "payments API key",
                "tracker license",
                "old contract",
            ],
        )

    def test_live_items_have_check_and_no_expires(self):
        tls, domain = load(FIXTURES / "valid.json")[:2]
        self.assertTrue(tls.is_live)
        self.assertEqual(tls.check, {"host": "example.com", "port": 443})
        self.assertIsNone(tls.expires)
        self.assertEqual(domain.check, {"domain": "example.com"})

    def test_manual_items_have_a_real_date(self):
        key = load(FIXTURES / "valid.json")[2]
        self.assertFalse(key.is_live)
        self.assertEqual(key.expires, date(2026, 10, 1))
        self.assertEqual(key.note, "rotate in dashboard")

    def test_tls_port_defaults_to_443(self):
        p = write_json(
            {
                "items": [
                    {"name": "t", "type": "tls", "owner": "o", "check": {"host": "example.com"}}
                ]
            }
        )
        self.assertEqual(load(p)[0].check["port"], 443)

    def test_whitespace_is_trimmed(self):
        p = one_item(name="  spaced  ", owner=" o@example.com ")
        item = load(p)[0]
        self.assertEqual(item.name, "spaced")
        self.assertEqual(item.owner, "o@example.com")


class ParsesDates(unittest.TestCase):
    # The loader sees two shapes for the same field: JSON gives a string, YAML gives a
    # date object for an unquoted YYYY-MM-DD. Both must land on the same value.
    def test_string_becomes_date(self):
        self.assertEqual(_parse_date("2026-10-01", "x"), date(2026, 10, 1))

    def test_date_object_passes_through(self):
        self.assertEqual(_parse_date(date(2026, 10, 1), "x"), date(2026, 10, 1))

    def test_other_types_are_refused(self):
        with self.assertRaises(InventoryError) as ctx:
            _parse_date(20261001, "x")
        self.assertIn("must be a date", str(ctx.exception))


@unittest.skipUnless(HAVE_YAML, "PyYAML not installed; run `uv sync --extra dev`")
class LoadsYamlInventory(unittest.TestCase):
    # YAML is the format the README tells people to write. It has to be tested end to
    # end, not inferred from the JSON tests passing.
    def test_yaml_and_json_fixtures_load_identically(self):
        self.assertEqual(load(FIXTURES / "valid.yaml"), load(FIXTURES / "valid.json"))

    def test_unquoted_yaml_date_is_accepted(self):
        p = write_text(
            "items:\n  - name: k\n    type: api-key\n    owner: o\n    expires: 2026-10-01\n",
            ".yaml",
        )
        self.assertEqual(load(p)[0].expires, date(2026, 10, 1))

    def test_yml_extension_works_too(self):
        p = write_text(
            "items:\n  - name: k\n    type: api-key\n    owner: o\n    expires: '2026-10-01'\n",
            ".yml",
        )
        self.assertEqual(load(p)[0].name, "k")

    def test_malformed_yaml_is_an_inventory_error(self):
        p = write_text("items:\n  - name: [unclosed\n", ".yaml")
        with self.assertRaises(InventoryError) as ctx:
            load(p)
        self.assertIn("not valid YAML", str(ctx.exception))

    def test_empty_yaml_file_is_an_inventory_error(self):
        # yaml.safe_load("") returns None, which is not an inventory.
        with self.assertRaises(InventoryError):
            load(write_text("", ".yaml"))


class RejectsBrokenInventory(unittest.TestCase):
    def assertRejects(self, path: Path, fragment: str):
        with self.assertRaises(InventoryError) as ctx:
            load(path)
        self.assertIn(fragment, str(ctx.exception))

    def test_missing_file(self):
        self.assertRejects(Path("/nonexistent/inventory.json"), "not found")

    def test_top_level_must_have_items(self):
        self.assertRejects(write_json({"things": []}), "'items'")

    def test_items_must_be_a_list(self):
        self.assertRejects(write_json({"items": {"a": 1}}), "must be a list")

    def test_missing_name(self):
        self.assertRejects(one_item(name=""), "'name' is required")

    def test_missing_owner(self):
        # An item with no owner is an item nobody will act on. That's the whole problem.
        self.assertRejects(one_item(owner=None), "'owner' is required")

    def test_manual_type_without_expires(self):
        self.assertRejects(one_item(expires=None), "needs an 'expires' date")

    def test_manual_type_with_check_block(self):
        self.assertRejects(one_item(check={"host": "x"}), "can't be checked live")

    def test_bad_date_format(self):
        self.assertRejects(one_item(expires="10/01/2026"), "YYYY-MM-DD")

    def test_live_type_without_check(self):
        p = write_json({"items": [{"name": "t", "type": "tls", "owner": "o"}]})
        self.assertRejects(p, "needs a 'check' block")

    def test_live_type_missing_required_key(self):
        p = write_json({"items": [{"name": "t", "type": "domain", "owner": "o", "check": {}}]})
        self.assertRejects(p, "missing: domain")

    def test_live_type_with_expires_is_refused(self):
        # A typed date on a live item would shadow whatever the tool actually finds.
        p = write_json(
            {
                "items": [
                    {
                        "name": "t",
                        "type": "tls",
                        "owner": "o",
                        "check": {"host": "h"},
                        "expires": "2027-01-01",
                    }
                ]
            }
        )
        self.assertRejects(p, "remove 'expires'")

    def test_duplicate_names(self):
        p = write_json(
            {
                "items": [
                    {"name": "same", "type": "license", "owner": "o", "expires": "2027-01-01"},
                    {"name": "same", "type": "license", "owner": "o", "expires": "2027-02-01"},
                ]
            }
        )
        self.assertRejects(p, "duplicate")

    def test_malformed_json_is_an_inventory_error(self):
        # A user with a typo should get a one-line message, not a traceback.
        self.assertRejects(write_text('{"items": [', ".json"), "not valid JSON")

    def test_unsupported_extension(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False)
        f.write("x = 1\n")
        f.close()
        self.assertRejects(Path(f.name), "unsupported extension")


if __name__ == "__main__":
    unittest.main()
