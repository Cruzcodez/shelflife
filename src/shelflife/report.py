"""Turn Items into Results, and Results into something a person can read.

This is where live checkers plug in. `evaluate` takes a mapping of type -> checker function. In
the first version that mapping is empty, so live items come back as "unchecked" and the report
says so plainly. Later versions register a checker per live type; nothing else changes.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date

from .models import Item, Result

# A checker takes an Item and returns the expiry date it found. It raises on failure; evaluate
# turns that into a Result with source="error" so one bad host never kills the whole run.
Checker = Callable[[Item], date]


def evaluate(items: list[Item], checkers: dict[str, Checker] | None = None) -> list[Result]:
    checkers = checkers or {}
    results: list[Result] = []
    for item in items:
        if not item.is_live:
            results.append(Result(item=item, expires=item.expires, source="inventory"))
            continue
        checker = checkers.get(item.type)
        if checker is None:
            results.append(Result(item=item, expires=None, source="unchecked"))
            continue
        try:
            results.append(Result(item=item, expires=checker(item), source="live"))
        except Exception as e:  # noqa: BLE001  (any failure is a report line, not a crash)
            results.append(Result(item=item, expires=None, source="error", error=str(e)))
    return results


def sort_for_report(results: list[Result], today: date) -> list[Result]:
    """Soonest first. Errors and unchecked items go to the top, because they're the ones you can't
    reason about, and burying them under a long list of healthy items is how they get missed."""

    def key(r: Result) -> tuple[int, int]:
        if r.source == "error":
            return (0, 0)
        if r.expires is None:
            return (1, 0)
        return (2, r.days_left(today))

    return sorted(results, key=key)


def exit_code(results: list[Result], today: date, threshold_days: int) -> int:
    """0 if everything is fine. 1 if anything is expiring or expired. 2 if anything couldn't be
    checked. Non-zero on trouble is what lets this run as a cron job or a CI step with no wiring."""
    statuses = {r.status(today, threshold_days) for r in results}
    if statuses & {"expired", "expiring"}:
        return 1
    if statuses & {"error", "unchecked"}:
        return 2
    return 0


def render_table(results: list[Result], today: date, threshold_days: int) -> str:
    rows = sort_for_report(results, today)
    if not rows:
        return "Inventory is empty.\n"

    header = ("STATUS", "DAYS", "EXPIRES", "TYPE", "NAME", "OWNER", "SOURCE")
    lines = []
    for r in rows:
        days = r.days_left(today)
        lines.append(
            (
                r.status(today, threshold_days).upper(),
                "" if days is None else str(days),
                "" if r.expires is None else r.expires.isoformat(),
                r.item.type,
                r.item.name,
                r.item.owner,
                r.source if not r.error else f"error: {r.error}",
            )
        )
    widths = [max(len(str(c)) for c in col) for col in zip(header, *lines, strict=True)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    out = [fmt.format(*header), fmt.format(*("-" * w for w in widths))]
    out += [fmt.format(*line) for line in lines]

    n_bad = sum(1 for r in rows if r.status(today, threshold_days) in ("expired", "expiring"))
    n_unknown = sum(1 for r in rows if r.status(today, threshold_days) in ("error", "unchecked"))
    out.append("")
    out.append(
        f"{len(rows)} items. {n_bad} within {threshold_days} days or already expired. "
        f"{n_unknown} could not be checked. Today is {today.isoformat()}."
    )
    return "\n".join(out) + "\n"


def render_json(results: list[Result], today: date, threshold_days: int) -> str:
    payload = {
        "today": today.isoformat(),
        "threshold_days": threshold_days,
        "items": [
            {
                "name": r.item.name,
                "type": r.item.type,
                "owner": r.item.owner,
                "status": r.status(today, threshold_days),
                "expires": r.expires.isoformat() if r.expires else None,
                "days_left": r.days_left(today),
                "source": r.source,
                "error": r.error or None,
                "note": r.item.note or None,
            }
            for r in sort_for_report(results, today)
        ],
    }
    return json.dumps(payload, indent=2) + "\n"
