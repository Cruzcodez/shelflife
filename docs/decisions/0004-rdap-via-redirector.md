# 4. Domain checks go through the rdap.org redirector

**Status:** Accepted
**Date:** 2026-09-14

## Context

RDAP is the registry protocol that replaced WHOIS. Every registry runs its own server, and the mapping from top-level domain to server lives in a bootstrap file that IANA publishes. To look up `example.com` you fetch the bootstrap file, find the `.com` entry, and query Verisign's server. To look up `example.org` you do the same and end up at PIR's server.

There are three ways to handle that in this tool.

Implement the bootstrap ourselves: fetch IANA's file, cache it, pick the server. Correct and self-contained, and about a hundred lines plus a cache with an expiry of its own, in a tool whose whole point is one file and one command.

Use a paid or keyed lookup API. Better coverage (some of them fall back to WHOIS for TLDs without RDAP), but the tool would need a credential, and the scope document rules out the tool holding credentials.

Use `https://rdap.org`, a free public redirector run by the RDAP community. You ask it for a domain and it answers with a redirect to the right registry server, or a 404 that says no server exists. Zero configuration, zero credentials, one HTTP request.

## Decision

The domain checker asks `rdap.org` and follows the redirect. The registry's answer is what gets parsed; `rdap.org` never sees or shapes the data, it only says where to go.

## Consequences

- If `rdap.org` is down or rate-limits, every `domain` item in a run reports as `error` and the exit code is 2. The report says so per item and the rest of the run is unaffected. That is the correct behavior under ADR 0002: the tool could not give a complete answer, and it says so instead of guessing.
- The tool has one external dependency at runtime that it does not control. For a proof of concept whose users run it from cron once a day, that is an acceptable trade against a hundred lines of bootstrap logic. If it becomes a problem in practice, the fix is to implement the bootstrap lookup behind the same `fetch` seam the tests already use, and this ADR gets superseded.
- TLDs with no RDAP server (`.de` is the well-known one) get a specific message telling the operator to track that domain with a manual date. This is the "falls back to a manual date" line in the scope document, made concrete: the fallback is a human decision recorded in the inventory, not something the tool does silently.
- The tool sends a `User-Agent` that names this project, so a registry operator looking at their logs can tell what is querying them.
