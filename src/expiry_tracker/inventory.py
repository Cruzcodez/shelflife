"""Load and validate the inventory file.

The inventory is YAML because that's what ops people edit. JSON with the same structure is also
accepted; see engagement/03-scope.md, where that was added to scope after the first review.

Validation is strict on purpose. A silently ignored item is an item that expires with nobody
watching, which is the exact failure this tool exists to prevent.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .models import LIVE_TYPES, Item

# What each live type needs in its `check` block. Nothing here is a secret: a hostname and a port,
# or a domain name. The inventory must never hold the thing itself.
REQUIRED_CHECK_KEYS: dict[str, tuple[str, ...]] = {
    "tls": ("host",),
    "domain": ("domain",),
}


class InventoryError(ValueError):
    """The inventory file is wrong in a way that would leave something untracked."""


def load(path: str | Path) -> list[Item]:
    """Read an inventory file and return validated Items. Raises InventoryError on any problem."""
    path = Path(path)
    if not path.exists():
        raise InventoryError(f"inventory file not found: {path}")

    raw = _read(path)
    if not isinstance(raw, dict) or "items" not in raw:
        raise InventoryError(f"{path}: top level must be a mapping with an 'items' list")
    if not isinstance(raw["items"], list):
        raise InventoryError(f"{path}: 'items' must be a list")

    items = [_parse_item(entry, index) for index, entry in enumerate(raw["items"])]

    names = [i.name for i in items]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise InventoryError(f"duplicate item names: {', '.join(dupes)}. Names must be unique.")
    return items


def _read(path: Path) -> object:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    try:
        if suffix == ".json":
            return json.loads(text)
        if suffix in (".yaml", ".yml"):
            import yaml  # noqa: PLC0415  (kept local so the JSON path never touches it)

            return yaml.safe_load(text)
    except (json.JSONDecodeError, ValueError) as e:
        raise InventoryError(f"{path}: not valid {suffix[1:].upper()}: {e}") from e
    except Exception as e:  # PyYAML raises its own hierarchy; surface it the same way
        if type(e).__module__.startswith("yaml"):
            raise InventoryError(f"{path}: not valid YAML: {e}") from e
        raise
    raise InventoryError(f"{path}: unsupported extension {suffix!r}; use .yaml, .yml, or .json")


def _parse_item(entry: object, index: int) -> Item:
    where = f"items[{index}]"
    if not isinstance(entry, dict):
        raise InventoryError(f"{where}: must be a mapping")

    name = _require_str(entry, "name", where)
    where = f"{where} ({name!r})"
    type_ = _require_str(entry, "type", where)
    owner = _require_str(entry, "owner", where)
    note = str(entry.get("note", "") or "")

    has_expires = "expires" in entry and entry["expires"] is not None
    has_check = "check" in entry and entry["check"] is not None

    if type_ in LIVE_TYPES:
        if not has_check:
            need = ", ".join(REQUIRED_CHECK_KEYS[type_])
            raise InventoryError(f"{where}: type {type_!r} needs a 'check' block with: {need}")
        if has_expires:
            raise InventoryError(
                f"{where}: type {type_!r} is checked live; remove 'expires' so a stale date "
                "can't shadow what the tool finds"
            )
        check = _parse_check(entry["check"], type_, where)
        return Item(name=name, type=type_, owner=owner, check=check, note=note)

    if has_check:
        raise InventoryError(
            f"{where}: type {type_!r} can't be checked live. Give it an 'expires' date instead."
        )
    if not has_expires:
        raise InventoryError(
            f"{where}: needs an 'expires' date (YYYY-MM-DD). "
            f"Only types {sorted(LIVE_TYPES)} can be checked live."
        )
    return Item(
        name=name, type=type_, owner=owner, expires=_parse_date(entry["expires"], where), note=note
    )


def _parse_check(check: object, type_: str, where: str) -> dict:
    if not isinstance(check, dict):
        raise InventoryError(f"{where}: 'check' must be a mapping")
    missing = [k for k in REQUIRED_CHECK_KEYS[type_] if not check.get(k)]
    if missing:
        raise InventoryError(f"{where}: 'check' is missing: {', '.join(missing)}")
    out = dict(check)
    if type_ == "tls":
        out["port"] = int(out.get("port", 443))
    return out


def _parse_date(value: object, where: str) -> date:
    # YAML hands back a real date for an unquoted YYYY-MM-DD; JSON hands back a string.
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError as e:
            raise InventoryError(f"{where}: 'expires' must be YYYY-MM-DD, got {value!r}") from e
    raise InventoryError(f"{where}: 'expires' must be a date, got {type(value).__name__}")


def _require_str(entry: dict, key: str, where: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InventoryError(f"{where}: '{key}' is required and must be non-empty text")
    return value.strip()
