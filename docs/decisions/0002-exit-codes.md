# 2. Exit codes are the alert

**Status:** Accepted
**Date:** 2026-09-14

## Context

The people this tool is for (discovery in [engagement/02-discovery.md](../../engagement/02-discovery.md)) do not want another dashboard to remember to look at. They want the thing that is about to expire to show up wherever they already are: a cron email, a failed CI job, a chat message. The cheapest way to plug into all of those at once is a process exit code. Every scheduler and every CI system already treats non-zero as "tell someone."

That only works if the codes mean one thing, forever. A script written today against `shelflife check` has to keep working after the live checks land, after the report format changes, and after whatever comes next. So the exit codes are a contract, and a contract needs to be written down somewhere the code can't quietly drift away from.

## Decision

`shelflife check` returns exactly one of three codes:

| Code | Meaning | What to do |
|------|---------|------------|
| `0` | Every item was checked and nothing is within the warning window. | Nothing. |
| `1` | At least one item is expiring inside the window or has already expired. | Act on the report. This is the alert. |
| `2` | The tool could not give a complete answer: the inventory file is missing or invalid, or at least one item could not be checked (a live check failed, or no checker exists for its type yet). | Fix the tool or the inventory. The report may still be useful but it is not trustworthy on its own. |

When both conditions are true, `1` wins. An item that is expiring is a real deadline; an item that could not be checked is a maintenance problem. If someone only reads the exit code, the deadline is the thing they must not miss. The report still lists the errors and unchecked items so nothing is hidden, they just don't override the alert.

Anything the tool prints on the way to `2` goes to stderr with an `error:` prefix. Stdout is reserved for the report so `--json` output can be piped without filtering.

The warning window is `--days`, default 30. Changing the default would change what `0` means for every existing cron job, so it stays at 30 unless a future ADR supersedes this one.

## Consequences

- A cron entry like `shelflife check || mail -s "expiry" ops@example.com` is a complete alerting setup. No wrapper script, no parsing.
- The three codes must stay stable across every future change. A new failure mode has to fit into `2`, not get its own number. If that ever becomes too coarse, that is a new ADR, not a quiet edit.
- The precedence rule means a run with one expiring item and ten broken checks exits `1`. Anyone who needs to catch the broken checks separately reads the `--json` output, where every item carries its own `status`.
- Tests in `tests/test_report.py` and `tests/test_cli.py` pin all three codes and the precedence rule. If those tests change, this document changes with them.

## Also recorded here: packaging

Small enough not to need its own ADR. The project uses `uv` for environments and `hatchling` as the build backend. `uv` because it is one tool for "create the environment, install the extras, run the checks" and it is fast enough that CI setup is not the slow part. `hatchling` because it is the smallest standard-compliant backend that needs no configuration beyond the package path. Neither choice constrains the code; either could be swapped in an afternoon.
