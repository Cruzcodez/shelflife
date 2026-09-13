# 2. Discovery

**Date:** 2026-09-13
**Decision:** build it

---

## What you looked at

Instead of interviewing people, I went and found people who'd already been burned and had written it up. Public post-mortems, outage notices, and help-forum posts. Five incidents in detail, one industry-wide policy change, and two Hacker News threads where people describe what they still do by hand.

- Crates.io certificate expiry post-mortem, November 2016
- GitLab issue #416991, Snowplow collector certificate expiry, July 2023
- University of Washington eOutage notice, sdb.admin.washington.edu, December 26, 2024
- A Shopify store owner locked out after a domain expiry, August 2024
- The Register's running list of certificate-caused outages: Firefox root cert (March 2025), Google Chromecast (March 2025), ServiceNow (September 2024), Microsoft SwiftKey (July 2024), Cisco SD-WAN (May 2023)
- DigiCert's summary of the CA/Browser Forum ballot on certificate lifetimes
- Hacker News: "What do you still do manually in 2026" and "What developer tool do you wish existed"

## What you found

Five incidents, and each one fails a different way. That's the important part. It's not one problem, it's four problems that look like one.

**The automation broke silently and nobody noticed.** Crates.io had automated renewal. It failed. They got a notification, checked manually a few times, and in their own words "forgot to check again." No persistent monitoring. Down for an hour and a half, every CI build depending on them failed.

**The inventory was wrong.** GitLab's Snowplow collector certificate expired and stayed expired for 22 hours. The service had been marked *defunct* in their certificate documentation, so nobody was watching it. It wasn't defunct. A developer found it by noticing errors in browser devtools.

**One expiry cascaded into another.** A Shopify store owner's domain expired. Their store login was tied to an email on that domain. Verification codes went to a dead mailbox. They couldn't log in to renew the domain that would bring the mailbox back. Locked out for two weeks at the time of posting. Their words: "when I receive the verification code to log in and renew the domain, it doesn't arrive because the domain is expired." This is the consolidation argument in one story. Nothing tracked the dependency between two things that expire.

**It expired when nobody was looking.** University of Washington's certificate expired December 26 at 5:42 PM. The day after Christmas.

**Big companies with big budgets still miss it.** Firefox's root certificate expiry broke add-ons for users worldwide. Chromecast devices stopped working the same week. ServiceNow, Microsoft, Cisco. These are not teams that lack tooling. They lack one place that knows about everything.

**And the volume is scheduled to multiply.** Certificate lifetimes: 398 days until March 2026, 200 days now, 100 days from March 2027, 47 days from March 2029. Domain validation reuse drops to 10 days. DigiCert's own line: manual tracking at that cadence "would be a recipe for failure and outages."

**What people say they want.** Reading between the lines of the Hacker News threads, the recurring wishes are: things I have to check in multiple places, things I want to be told about instead of checking, and tools that don't break when nobody's watching. Someone described their situation as "lots of moving pieces, no sync, huge mess."

## Assumptions

| What you're assuming | How you'd confirm it | What breaks if it's wrong |
| --- | --- | --- |
| A TLS certificate's expiry can be read by opening a connection to the host, with no credentials | Python's `ssl` module, one function, test against any public site | Nothing. This one is well known. Listed so it's on record. |
| Domain expiry can be read from RDAP (the successor to WHOIS) without a paid API, for common TLDs | Query `rdap.org` for three domains on different TLDs | Domains become a manual-date item like API keys. Less useful, still works. |
| API keys, licenses, and similar have no queryable expiry and must be entered by hand | True by nature. Confirm by not finding a counterexample in the first five item types. | Nothing breaks. If some type turns out checkable, that's a feature later. |
| A YAML file is a reasonable inventory format for a non-engineer to edit | Hand the sample file to someone who doesn't code and ask them to add a row | Switch to CSV. Small change. |
| A webhook is enough for alerting in the first version | It is, by definition. Slack and email both accept webhooks. | Nothing. Native integrations are out of scope anyway. |
| The swarm will catch real problems in this codebase | Run it on every PR. Count what it finds that I didn't. | The swarm needs work, not this project. That's a finding, not a failure. |

## Constraints

- Technical: Python 3.11 or newer. Standard library where possible. No cloud SDKs in the core.
- Access: none needed. Everything the tool checks is public (a cert on a public host, a domain's registration record) or entered by hand.
- Time: first working version by 2026-09-27.
- Money: nothing to run. No paid APIs in scope.
- Political: none. If this later gets handed to a customer, the handoff document is the deliverable.

## Options you considered

**Option A: build the consolidated tracker.**
- How it works: one inventory file listing everything that expires, with type, identifier, owner, and either a live check or a manual date. One command reports what's coming due.
- Good because: one place, one report, every type. The thing that doesn't exist. Small enough to finish.
- Bad because: single-purpose tools do each individual check better. This one has to be good enough at all of them.

**Option B: wire together existing single-purpose tools.**
- How it works: a cert monitor, a domain monitor, and a shared calendar for everything else.
- Good because: each tool is mature.
- Bad because: three tools, three places to look, and the calendar is still a human remembering. This is what people already do, and it's the setup that failed in every incident above.

**Option C: a spreadsheet with dates and a reminder.**
- How it works: exactly what it sounds like.
- Good because: zero build.
- Bad because: no live checks, so the inventory drifts from reality. GitLab's inventory said "defunct." Crates.io's process said "renewed." Both were wrong and nothing checked.

**Doing nothing.** Keep finding out from outages. Rejected, and every incident above is the reason.

Chose A.

## What it would take

- Effort: a first version in a few evenings. The live checks are the only real code. The rest is reading a file and printing a table.
- What it costs to run: nothing. A cron job on any machine.
- What you'd need access to: nothing beyond a network connection.
- Biggest thing that could go wrong: I get a false sense of safety from a tool that has a gap, the same way GitLab did from a document that said "defunct." Mitigation: the report says plainly what it checked live and what it's taking on faith from the inventory.

---

## Decision

> **Decision:** build it
>
> **Because:** the problem is universal, every incident I found has a distinct failure mode that a consolidated tracker addresses, the industry just made it measurably worse on a fixed schedule, and the first version is small enough to finish in two weeks. Also, it gives the swarm a real codebase with real security decisions in it (never store the secret, only its metadata), which is the second thing this project is for.

### If you're building: what would make you stop

> **Still worth it if:** by 2026-09-27 the tool reads an inventory of at least five items across at least three types, live-checks certificates and domains correctly against real hosts, prints a report a non-engineer could act on, and the swarm has reviewed at least three pull requests and caught at least one thing I didn't.
>
> **Check by:** 2026-09-27
>
> If the live checks can't be made reliable, the tool is a spreadsheet with extra steps and I stop. If the swarm reviews three PRs and catches nothing, the swarm is the problem and I go fix that first.
