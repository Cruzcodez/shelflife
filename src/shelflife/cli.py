"""Command line entry point.

    shelflife check --inventory inventory.yaml --days 30
    shelflife check --inventory inventory.yaml --json > report.json

Exit code is 0 when nothing needs attention, 1 when something is expiring or expired, and 2 when
something couldn't be checked. That's so a cron job or a CI step can act on it with no parsing.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from . import __version__
from .checkers import CHECKERS
from .inventory import InventoryError, load
from .report import evaluate, exit_code, render_json, render_table


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="shelflife",
        description="Report on everything in your inventory that's about to expire.",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="read the inventory and report what's coming due")
    check.add_argument(
        "--inventory",
        "-i",
        default="inventory.yaml",
        help="path to the inventory (default: %(default)s)",
    )
    check.add_argument(
        "--days",
        "-d",
        type=int,
        default=30,
        help="warn when within this many days (default: %(default)s)",
    )
    check.add_argument("--json", action="store_true", help="output JSON instead of a table")
    check.add_argument(
        "--offline",
        action="store_true",
        help="skip live checks; live items report as unchecked (exit code 2)",
    )
    check.add_argument(
        "--today", type=date.fromisoformat, default=None, help=argparse.SUPPRESS
    )  # for tests and for "what would this look like next month"
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "check":  # pragma: no cover  (argparse enforces this)
        return 2

    today = args.today or date.today()
    try:
        items = load(args.inventory)
    except InventoryError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    results = evaluate(items, {} if args.offline else CHECKERS)
    output = render_json if args.json else render_table
    sys.stdout.write(output(results, today, args.days))
    return exit_code(results, today, args.days)
