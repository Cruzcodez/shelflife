# expiry-tracker

One place that knows about everything you have that expires, and tells you before it does.

Certificates, domains, API keys, licenses, contracts. They live in different systems, get tracked by different people, and the one that takes you down is always the one nobody owned. This is a command-line tool that keeps one inventory of all of them, checks the ones it can check live, and reports what's coming due with an owner next to each.

It watches. It never renews anything, and it never stores the secret itself. Names and dates only.

## Why this exists

Every team has had the outage. Crates.io went down because an automated renewal failed silently and someone "forgot to check again." GitLab's analytics collector was dark for 22 hours because the certificate was marked defunct in a document and wasn't. A Shopify store owner was locked out for two weeks because their domain expired and their login email was on that domain. The University of Washington's certificate expired the day after Christmas.

And it's getting worse on a schedule. The CA/Browser Forum cut TLS certificate lifetimes from 398 days to 200 in March 2026, to 100 in March 2027, and to 47 in March 2029. Whatever you were tracking by hand, you're about to track it four to eight times as often.

The full reasoning, with sources, is in [engagement/02-discovery.md](engagement/02-discovery.md).

## Status

Proof of concept, in progress. Scope is in [engagement/03-scope.md](engagement/03-scope.md). Nothing to run yet.

## What's in here

| Path | What |
| --- | --- |
| `engagement/` | Why this exists, what was found, what's in and out of scope, and (later) how to take it over |
| `docs/decisions/` | Decisions that would be expensive to reverse, recorded as they're made |
| `scripts/check.sh` | The one command that says whether the repo is healthy. CI runs exactly this. |
| `AGENTS.md` | Working agreement for any AI agent that touches this code |
| `.kiro/steering/` | Standards the agents follow |

Generated from [project-starter](https://github.com/Cruzcodez/project-starter). Every pull request is reviewed by [agentic-swarm](https://github.com/Cruzcodez/agentic-swarm) before it merges.

## License

MIT. See [LICENSE](LICENSE).
