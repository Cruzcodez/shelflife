# Landscape

What else exists, and how shelflife compares. Written 2026-09-14, before the repository went public, from a read of 51 repositories: 21 in shelflife's own space (certificate and domain expiry monitoring; 19 appear in the table below, and two that are archived, Netflix's lemur and RaymiiOrg's certificate-expiry-monitor, are left out of it), 10 security and operations CLIs, 10 widely admired command-line tools, and 10 well-regarded Python projects. Star counts are as of that day and will drift. The point is not the numbers, it is what the field does and does not do.

## The tools that do the same job

| Tool | Stars | Shape | TLS expiry | Domain expiry | Other expiring things | Owner per item | Exit code documented |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [uptime-kuma](https://github.com/louislam/uptime-kuma) | 90k | server + UI | yes | no | no | no | n/a (server) |
| [gatus](https://github.com/TwiN/gatus) | 12k | server + UI, YAML | yes | yes | no | no | n/a (server) |
| [blackbox_exporter](https://github.com/prometheus/blackbox_exporter) | 5.9k | Prometheus exporter | metric only | no | no | no | n/a |
| [certspotter](https://github.com/SSLMate/certspotter) | 1.2k | CT log monitor | issuance, not expiry | no | no | no | no |
| [x509-certificate-exporter](https://github.com/enix/x509-certificate-exporter) | 931 | Prometheus exporter, K8s | yes | no | CRLs | no | n/a |
| [ssl-cert-check](https://github.com/Matty9191/ssl-cert-check) | 783 | shell script | yes | no | no | no | no |
| [domainmod](https://github.com/DomainMOD/domainmod) | 597 | PHP web app | yes | yes | hosting, IPs | no | n/a |
| [ssl_exporter](https://github.com/ribbybibby/ssl_exporter) | 595 | Prometheus exporter | yes | no | no | no | n/a |
| [maintenant](https://github.com/kOlapsis/maintenant) | 476 | server + UI | yes | no | image digests | no | n/a |
| [check_ssl_cert](https://github.com/matteocorti/check_ssl_cert) | 414 | Nagios plugin | yes | no | no | no | Nagios codes, undocumented in README |
| [cert-exporter](https://github.com/joe-elliott/cert-exporter) | 388 | Prometheus exporter, K8s | yes | no | no | no | n/a |
| [ssl-checker](https://github.com/narbehaj/ssl-checker) | 322 | Python CLI | yes | no | no | no | yes (0/1/2) |
| [domain-monitor](https://github.com/Hosteroid/domain-monitor) | 249 | PHP web app | yes | yes | no | no | n/a |
| [certificate-expiry-monitor](https://github.com/muxinc/certificate-expiry-monitor) | 170 | Prometheus exporter, K8s | yes | no | no | no | n/a |
| [websites-monitor](https://github.com/fabriziosalmi/websites-monitor) | 56 | GitHub Action + API | yes | yes | no | no | no |
| [check-ssl-cert-expire-date](https://github.com/codex-team/check-ssl-cert-expire-date) | 31 | cron script | yes | yes (whois) | no | no | no |
| [sslcheck](https://github.com/i04n/sslcheck) | 23 | single-file Python CLI | yes | no | no | no | yes (0/1) |
| [domain-check](https://github.com/ashworthconsulting/domain-check) | 16 | shell script | no | yes | no | no | no |
| [tls-monitor](https://github.com/zrosenbauer/tls-monitor) | 11 | GitHub Action | yes | no | no | no | no |
| **shelflife** | 0 | CLI, one file in | yes | yes | any: api-key, license, contract, anything with a date | **yes** | **yes (0/1/2, ADR)** |

Three things fall out of that table.

**Nobody tracks the non-network things.** Every tool here is about certificates, and a few add domains. API keys, licenses, contracts, warranties, the things that expire on a calendar rather than on a wire, are not in any of them. The outage stories in [02-discovery](../engagement/02-discovery.md) say those are the ones nobody owns.

**Nobody puts an owner next to an item.** The report says what is expiring. None of them say who is supposed to do something about it.

**The exit code is an afterthought everywhere.** Two of nineteen document it. The Prometheus tools do not have one. shelflife's [ADR 0002](decisions/0002-exit-codes.md) makes it the primary interface, which is either the whole idea or a mistake, and only real use will say which.

## Where shelflife is behind

Honest list, because the table above flatters.

- **No Prometheus output.** Every Go tool in the space is Prometheus-first, and that is the lingua franca for the people most likely to care. `--prometheus` is one function and is on the list.
- **No dashboard, no status page.** The two most-used tools in the space (uptime-kuma, gatus) are built around one. shelflife's answer is a static HTML report published by CI, which is not the same thing and is not meant to be. See "When not to use this" in the README.
- **No single-target mode.** Every script in the space takes `-H host` and answers immediately. shelflife needs a file. That is a deliberate choice (the file is the point) but it costs the five-second try-it-out.
- **No retries.** A flaky network reads as a failed check. Most of the field has the same limitation and does not say so; shelflife says so in the handoff.
- **Fewer alert sinks.** uptime-kuma has ninety. shelflife has one webhook and an exit code, on purpose.

## What the admired READMEs do, and what shelflife took from them

From the 30 repositories outside the space, the pattern above the fold is nearly universal: three to five functional badges, one-sentence pitch, a screenshot or terminal demo, an install command, all within one screen. Seven of ten have a visual. Nine of ten have a CONTRIBUTING file. Zero of ten put "how to run the tests" in the README; it lives in CONTRIBUTING. Only ripgrep has an explicit "why this exists" section, and only ripgrep has a "why you should not use this" section. Comparison-to-alternatives sections are rare; where they exist (hadolint, maintenant, ripgrep) they name the competitors.

Adopted, in this order: real terminal output under the pitch; badges for CI, Python version, license, and the review process; a one-line install that works from the repository without a package index; a "When not to use this" section that names the alternatives; CONTRIBUTING, SECURITY, CHANGELOG, a tagged release, and a pre-commit configuration.

Deliberately not adopted: a README that doubles as the manual (bat, just, fzf run to thousands of lines; shelflife's whole surface fits on one screen), testimonials and sponsor sections, chat badges, and a benchmark chart, because speed is not the pitch.

## Method

Five parallel readers, each given ten repositories and the same rubric: stars, language, license, activity, what it does, how targets are configured, what it checks, how it reports, dependencies, README length and headings in order, install one-liner, visual demo, badges, comparison section, governance files, one thing worth copying, one thing that is weak. Readers fetched repository pages and raw READMEs; GitHub's search and API were not used. Star counts are the number shown on the page that day.
