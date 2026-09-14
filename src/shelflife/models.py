"""The two shapes everything else works with: an Item you track, and a Result of looking at it."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

# Types the tool can check by itself, without a date in the inventory.
# Everything else (api-key, license, contract, whatever) needs an `expires` date entered by hand,
# because there's nothing to query.
LIVE_TYPES = frozenset({"tls", "domain"})


@dataclass(frozen=True)
class Item:
    """One thing that expires, as described in the inventory file.

    Exactly one of `expires` or `check` is set. `expires` is a date someone typed in.
    `check` is what the tool needs to look it up live (a host and port, a domain name).
    """

    name: str
    type: str
    owner: str
    expires: date | None = None
    check: dict | None = None
    note: str = ""

    @property
    def is_live(self) -> bool:
        return self.type in LIVE_TYPES


@dataclass(frozen=True)
class Result:
    """What we found out about an Item.

    `source` says where the expiry date came from, and it's the most important field in the
    report. "inventory" means someone typed the date and nothing verified it. "live" means the tool
    checked just now. A reader has to be able to tell those apart, because an inventory that says
    "defunct" or "renewed" can be wrong, and the whole point is to not trust it blindly.
    """

    item: Item
    expires: date | None
    source: str  # "inventory" | "live" | "unchecked" | "error"
    error: str = ""

    def days_left(self, today: date) -> int | None:
        if self.expires is None:
            return None
        return (self.expires - today).days

    def status(self, today: date, threshold_days: int) -> str:
        """One word for the report: expired, expiring, ok, unchecked, or error."""
        if self.source == "error":
            return "error"
        if self.expires is None:
            return "unchecked"
        days = self.days_left(today)
        if days < 0:
            return "expired"
        if days <= threshold_days:
            return "expiring"
        return "ok"
