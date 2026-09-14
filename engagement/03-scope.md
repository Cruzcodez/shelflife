# 3. Scope

**Date:** 2026-09-13
**Confirmed with:** Chris Cruz, 2026-09-14 (re-confirmed the same day, after the JSON input and `--offline` additions below)

---

## What we're building

A command-line tool that keeps one inventory of everything that expires (certificates, domains, API keys, licenses, anything with a date), checks the ones it can check live, and reports what's coming due, with an owner next to each item. It watches. It never renews, rotates, or stores the thing itself.

## In scope

- [ ] An inventory file in YAML. Each item has a type, a name, an owner, and either something to check live or a date entered by hand.
- [ ] The same inventory structure in JSON is also accepted. **Added 2026-09-14 after the first review**: the first PR shipped this without it being in scope. It's kept because a script generating the inventory will emit JSON more easily than YAML, and the cost is one branch in the loader. Re-confirmed 2026-09-14.
- [ ] Live check for TLS certificates: connect to `host:port`, read the expiry off the cert. No credentials.
- [ ] Live check for domain registrations via RDAP. Falls back to a manual date if the TLD doesn't support it.
- [ ] Manual-date items for everything else: API keys, licenses, contracts, warranties, whatever.
- [ ] `check` command: report everything expiring within N days (default 30), sorted soonest first, showing type, name, owner, days left, and whether the date was checked live or taken from the inventory.
- [ ] `check --offline`: same report with the live checks skipped, so the inventory can be read on a machine with no network. **Added 2026-09-14** during the live-checks PR; it fell out of keeping the tests off the network and was cheap to expose.
- [ ] Exit code: nonzero if anything is inside the warning window, so it works as a cron job or a CI step with no extra wiring.
- [ ] One alert output beyond the terminal: a generic webhook POST with the report as JSON. Slack, Discord, Teams, and email gateways all accept one.
- [ ] A sample inventory that works out of the box against public hosts, so `git clone` then `check` produces a real report in under a minute.
- [ ] Tests for the date math and for each checker, using recorded responses so they don't need the network.

## Out of scope

Parked, not refused.

- **Renewing or rotating anything.** This tool watches. The moment it acts, it needs credentials to everything it watches, and the security story becomes a different project. Phase two at the earliest, and probably never in this repo.
- **Storing secret values.** Not a feature to add later. A rule. Certificate private keys, API key values, passwords: the inventory holds names and dates, never contents.
- **A web interface or dashboard.** The report is the interface. If someone wants a page, the JSON output feeds one.
- **Native integrations** for Slack, email, PagerDuty, and so on. The webhook covers them. A native integration is a maintenance obligation per vendor.
- **Cloud provider integrations** (pull certs from ACM, domains from Route 53, secrets from Secrets Manager). Genuinely useful and genuinely the second version. Keeping the core cloud-free is the point of the first.
- **Multi-user, auth, roles.** One inventory file, one team, trust the filesystem.
- **Tracking dependencies between items** (the Shopify problem: this domain expiring breaks that login). Real and interesting. Also a graph problem, and the first version is a list.
- **Windows support.** Should work, won't be tested.

## Acceptance criteria

- [ ] From a fresh clone, `pip install` and one command produce a report against the sample inventory, with at least one real certificate and one real domain checked live.
- [ ] Given an inventory with a certificate expiring in 10 days and a threshold of 30, the report lists it and the exit code is nonzero. With a threshold of 5, it's absent and the exit code is zero.
- [ ] Given a host that doesn't respond, the report says so for that item and still reports everything else. One bad host doesn't kill the run.
- [ ] The report visibly distinguishes "checked live just now" from "date from the inventory file." A reader can tell which numbers to trust.
- [ ] A grep of the repository for anything that looks like a credential finds nothing.
- [ ] Someone who has never seen the project reads the README and can add a new item to the inventory without asking a question.

## Not production ready

This is a proof of concept. Before anyone relies on it:

- It runs when something runs it. There's no built-in scheduler. Cron or a CI job is the operator's problem, and the README says so.
- RDAP coverage varies by TLD. Some domains will fall back to manual dates and the report will say so, but a reader could miss it.
- No retry or backoff on network checks. A flaky connection reads as a failed check.
- The webhook posts with no authentication. Anyone who has the URL can be posted to. Fine for a Slack incoming webhook, not fine for anything that trusts the payload.
- Nobody has run it for a month to see whether the alerts are useful or annoying.

## What happens when scope changes

1. Write it down under Out of scope
2. Decide whether it replaces something in scope or extends the date
3. Update the date and the confirmed-with line
