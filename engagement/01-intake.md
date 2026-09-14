# 1. Intake

**Date:** 2026-09-13
**Who asked:** Chris Cruz. My own idea, but the customer is any team that has things that expire, which is every team.
**Who's building it:** Chris Cruz, with Claude

---

## What they asked for

The way I said it:

> A tool that shows real thought and does what any good app should do, which is consolidate dispersed systems. Because you may have a tool that tracks secret rotation, or domain renewals, but what about one that does it all?

Followed by:

> Something that anyone can understand. Not a calculator. General enough that most customers relate to it, specific enough and difficult enough that it can be built and documented properly.

## Why they want it

Two layers to this.

**The universal one.** Every business has had the outage where something quietly expired and nobody knew it was coming. A certificate, a domain, an API key, a license. It's not a technical problem, it's a "nobody was looking" problem. The things that expire live in different systems, get tracked in different spreadsheets by different people, and the one that matters is always the one nobody owned.

**The reason it's worse now.** In April 2025 the CA/Browser Forum voted to cut TLS certificate lifetimes. The maximum dropped from 398 days to 200 on March 15, 2026, six months ago. It drops to 100 days in March 2027 and to 47 days in March 2029. Every team that tracks certificates by hand just had its renewal workload double, and it's scheduled to double again, and again. The tools that track one kind of thing exist. The thing that doesn't exist for most teams is one place that knows about all of it.

## What does success look like

- I never find out about an expiration from an outage. I find out from the tool, with time to act.
- One command shows everything expiring in the next N days, across every type, sorted by when, with an owner next to each.
- It works without a cloud account. A laptop and a cron job is enough.
- A person who doesn't know what a TLS certificate is can read the report and know who to call.

## Constraints already on the table

- Budget: my time and tokens.
- Deadline: a working first version by 2026-09-27. That's the kill-condition date in discovery.
- Tools or platforms they have to use: Python, because it's what I read and write best. Git and GitHub with the full PR workflow.
- Tools or platforms they can't use: nothing cloud-specific in the core. Cloud integrations are a later feature, not a dependency.
- Security or compliance requirements: the tool tracks *when things expire*. It must never store the things themselves. No certificate private keys, no API key values, no passwords. Metadata only. This is a hard rule.
- Who has to approve things: me. Scope gets my name and a date.

## What you don't know yet

- [ ] Which types can be checked live (connect to a host and read the cert's expiry) versus which have to be entered by hand (an API key has no expiry you can query)
- [ ] How to check domain expiry reliably without a paid API. WHOIS is inconsistent; RDAP might be better.
- [ ] Where alerts go. Print to terminal is the floor. Email, Slack, and a webhook are the candidates.
- [ ] How much to automate. Watching is in. Renewing is probably out, at least at first.
- [ ] What the inventory file looks like. YAML, probably. Needs to be something a non-engineer could edit.
