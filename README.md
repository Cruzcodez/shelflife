# shelflife

Everything you own has a shelf life. This is the one place that knows all of them, and tells you before one runs out.

Certificates, domains, API keys, licenses, contracts. They live in different systems, get tracked by different people, and the one that takes you down is always the one nobody owned. This is a command-line tool that keeps one inventory of all of them, checks the ones it can check live, and reports what's coming due with an owner next to each.

It watches. It never renews anything, and it never stores the secret itself. Names and dates only.

## Why this exists

Every team has had the outage. Crates.io went down because an automated renewal failed silently and someone "forgot to check again." GitLab's analytics collector was dark for 22 hours because the certificate was marked defunct in a document and wasn't. A Shopify store owner was locked out for two weeks because their domain expired and their login email was on that domain. The University of Washington's certificate expired the day after Christmas.

And it's getting worse on a schedule. The CA/Browser Forum cut TLS certificate lifetimes from 398 days to 200 in March 2026, to 100 in March 2027, and to 47 in March 2029. Whatever you were tracking by hand, you're about to track it four to eight times as often.

The full reasoning, with sources, is in [engagement/02-discovery.md](engagement/02-discovery.md).

## Running it

You need Python 3.11 or newer and [uv](https://docs.astral.sh/uv/). From a fresh clone:

```bash
uv sync
uv run shelflife check --inventory inventory.example.yaml
```

If you're going to change the code, use `uv sync --locked --extra dev` instead. That's what CI installs, and it's what makes `scripts/check.sh` run the same checks locally that gate a pull request. `--locked` means you get exactly the versions in `uv.lock`; if you add a dependency, run `uv lock` and commit the result.

That reads the example inventory, checks the certificate on `example.com` and the registration of `example.com` live, and prints a table: what's expired, what's expiring within 30 days, what's fine, and what couldn't be checked. Change the window with `--days 14`. Get JSON with `--json`. Add `--offline` to skip the live checks and just read the file.

The exit code is the point. `0` means nothing needs attention. `1` means something is expiring or already expired. `2` means something couldn't be checked. Put it in a cron job or a CI step and the non-zero exit is your alert, no parsing needed.

## The inventory

One entry per thing that expires. Copy `inventory.example.yaml` and edit it. Every entry has a name, a type, and an owner, then either:

- a `check` block, for the types the tool can look up live: `tls` (a host and port) and `domain` (a domain name)
- an `expires` date, for everything else: `api-key`, `license`, `contract`, `warranty`, any word you like

The file holds names and dates. It never holds the thing itself. No certificate keys, no API key values, no passwords. That's the whole security model and it's what makes the inventory safe to commit.

JSON works too, same structure, if a script is generating it.

## Reading the report

The `SOURCE` column matters more than it looks. `inventory` means somebody typed that date and nothing has verified it. `live` means the tool checked just now. `unchecked` means it's a live type but the check was skipped (`--offline`). `error` means the check was attempted and failed, and the reason is right there in the row.

## How the live checks work

**`tls`**: the tool connects to the host and port, completes a TLS handshake, reads the expiry date off the certificate the server presents, and disconnects. It sends nothing else. It does not verify the certificate, on purpose: an expired or self-signed certificate is exactly what you want reported, and verification would refuse it before the date could be read. [ADR 0003](docs/decisions/0003-tls-checker-does-not-verify.md) has the reasoning.

**`domain`**: the tool asks [RDAP](https://about.rdap.org/), the registry protocol that replaced WHOIS, when the registration expires. Not every top-level domain has an RDAP server (`.de` is a well-known example). When that happens the report says so and tells you to track that domain with a manual date instead: change its type to something like `domain-manual` and give it an `expires` line.

Both checks time out after ten seconds. A host that does not answer becomes one `error` row and the rest of the report still runs.

Unchecked and errored items sort to the top. They're the ones you can't reason about, and burying them under a long list of healthy rows is how they get missed.

## Status

Proof of concept. What works: the inventory format, validation that refuses anything ambiguous, live checks for TLS certificates and domain registrations, the report, the exit codes. What doesn't yet: the webhook alert, which is the next pull request. Scope is in [engagement/03-scope.md](engagement/03-scope.md).

## What's in here

| Path | What |
| --- | --- |
| `engagement/` | Why this exists, what was found, what's in and out of scope, and (later) how to take it over |
| `docs/decisions/` | Decisions that would be expensive to reverse, recorded as they're made |
| `scripts/check.sh` | The one command that says whether the repo is healthy. CI runs exactly this. |
| `AGENTS.md` | Working agreement for any AI agent that touches this code |
| `.kiro/steering/` | Standards the agents follow |

Built from [project-starter](https://github.com/Cruzcodez/project-starter). Pull requests are reviewed by [agentic-swarm](https://github.com/Cruzcodez/agentic-swarm) before they merge; what it caught is in [docs/review-log.md](docs/review-log.md).

## License

MIT. See [LICENSE](LICENSE).
