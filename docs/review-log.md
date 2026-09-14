# Review log

Every pull request on this project gets reviewed by the [agentic-swarm](https://github.com/Cruzcodez/agentic-swarm) before a human looks at it. This file records what that review actually produced, PR by PR, so the claim "built with the swarm" comes with numbers instead of vibes.

Each entry answers the same questions. What did the swarm flag? Which of those would a tired human reviewer have missed? What did I override, and why? And what changed in the swarm itself because of this PR? That last one matters most: a review tool that never gets corrected by real use is a review tool nobody trusts.

Scoring rules, so the numbers mean the same thing every time:

- **Blocking / Should fix / Noted** are the swarm's own severities, copied as-is.
- **Accepted** means the fix landed in the same PR. **Deferred** means it became a tracked follow-up. **Overridden** means I disagreed and did not act, with the reason written here.
- **Would have missed** is my honest guess at whether I would have caught it reading the diff myself once, at the end of a long day. It is subjective. It is still the number that decides whether this is worth running.

---

## PR 1: inventory format, validation, report, and CLI

**Reviewed:** 2026-09-14
**Agents that ran:** security-reviewer, docs-reviewer, infra-reviewer, test-reviewer, scope-reviewer (merged by swarm)
**Verdict:** BLOCK
**Wall clock:** about 4 minutes for all five agents plus the merge
**Diff size:** 14 files, roughly 900 lines added

### Findings

| # | Severity | Finding | Agent | Outcome | Would have missed? |
|---|----------|---------|-------|---------|--------------------|
| 1 | Blocking | The YAML loading path had zero tests. Every fixture was JSON, but YAML is the documented default and the only format in the README. | test-reviewer | Accepted: added `tests/fixtures/valid.yaml`, a YAML-vs-JSON identity test, unquoted-date test, `.yml` test, and direct tests of `_parse_date` | Yes. I wrote the JSON fixtures on purpose because PyYAML was not installable in my sandbox, and I had talked myself into "the branch is tiny, it's fine." |
| 2 | Blocking | Exit codes `1` and `2` are a public contract for cron and CI users, but nothing recorded the decision or the precedence rule. Scope only promised "nonzero." | scope-reviewer, docs-reviewer | Accepted: [ADR 0002](decisions/0002-exit-codes.md) | Partly. I knew the codes were a contract, I would not have written the ADR before merging. |
| 3 | Blocking | JSON input shipped as a documented feature but scope said YAML only. The stated reason in a code comment ("so JSON users don't need PyYAML") was not true, since PyYAML is a hard dependency. | scope-reviewer | Accepted: scope doc updated with the change and a re-confirm flag; the misleading comment and its dead branch removed | Yes. This is the one that stings. JSON was there to make my tests easier and I dressed it up as a feature. The reviewer called the rationalization by name. |
| 4 | Should fix | README says `uv sync` but CI runs `uv sync --extra dev`, so following the README gives a weaker local check than the one that gates the PR. | docs-reviewer | Accepted: README paragraph added | Probably. |
| 5 | Should fix | A syntax error in the inventory file produced a raw traceback instead of the `error: ...` line and exit `2` the CLI promises. No test covered it. | test-reviewer | Accepted: parse errors now raise `InventoryError`; tests for malformed JSON, malformed YAML, and empty YAML | Yes. I never fed it a broken file. |
| 6 | Should fix | No `uv.lock` committed and open-ended version bounds, so CI resolves fresh every run and is not reproducible. | infra-reviewer | Deferred: `uv` cannot reach PyPI from where the code was written. Chris runs `uv lock` on his Mac in a follow-up commit and CI switches to `--locked`. | Yes. |
| 7 | Should fix | uv and hatchling chosen with no recorded reason. | scope-reviewer | Accepted: short packaging note at the bottom of ADR 0002 rather than a separate ADR, which the reviewer itself suggested | No, but I would not have written it down either. |
| 8 | Handoff | The "PyYAML is optional" branch was dead code. scope-reviewer noticed it and routed it to a "code-reviewer" that does not exist in the swarm. | scope-reviewer | Accepted: branch removed as part of finding 3 | Maybe. |

**Totals:** 3 blocking, 4 should fix, 1 handoff. 7 accepted, 1 deferred, 0 overridden. Would have missed: 5 of 8.

### Confirmed non-issues

Worth recording because a review that only lists problems trains you to skim it. The swarm checked and cleared: `yaml.safe_load` in use rather than `yaml.load`; CI carries no cloud credentials and already restricts `permissions` to `contents: read`; action pins on version tags accepted because nothing in the workflow touches credentials or deploys; `--inventory` accepting any local path is fine for a local CLI.

### Overrides

None. Every finding was either fixed in this PR or deferred with a named owner.

### What changed in the swarm because of this PR

One defect in the swarm itself. scope-reviewer handed a finding to an agent called "code-reviewer" that is not in the roster, and the swarm merge step correctly caught it under "Handoffs nobody picked up" rather than dropping it. That is the right failure mode, but the root cause is that the shared review contract does not list the actual roster, so an agent guessing at a teammate's name has nothing to check against. Fix tracked in the agentic-swarm repo: the review contract and each charter get the real roster, and the seed suite gets a case that expects a handoff to be routed to a real agent. Logged in that repo's `docs/eval-log.md`.

### What the human did that the swarm did not

Two things. The swarm noted that the scope document's "confirmed with" line was still a blank placeholder. It was right, but that was a process step waiting on Chris, not a code change; he signed it before this PR merged. And the swarm did not question whether the whole PR was too big for one review. Fourteen files is at the edge. Next PR is smaller.

---

## PR 3: live checks for TLS certificates and domain registrations

**Reviewed:** 2026-09-14
**Agents that ran:** security-reviewer, docs-reviewer, infra-reviewer, test-reviewer, scope-reviewer (merged by swarm)
**Verdict:** BLOCK
**Wall clock:** 5 minutes 28 seconds for all five agents plus the merge
**Diff size:** 13 files, roughly 700 lines added

(PR 2 was the lock file, one commit, no swarm review. It was itself a swarm finding from PR 1.)

### Findings

| # | Severity | Finding | Agent | Outcome | Would have missed? |
|---|----------|---------|-------|---------|--------------------|
| 1 | Blocking | The TLS checker's timeout branch had no test, and it is the one failure mode the README promises to handle. | test-reviewer | Accepted: injected `TimeoutError` test | Yes. |
| 2 | Blocking | The RDAP checker's network-failure and timeout branches were untested; every test fed it a canned response, none made the fetch raise. | test-reviewer | Accepted: two injected-exception tests | Yes. |
| 3 | Blocking | Valid JSON of the wrong shape (an array) hit an untested guard. | test-reviewer | Accepted | Probably. |
| 4 | Blocking | The DER parser's length-field validation was untested. The reviewer's point: this PR is what makes that parser reachable from an unverified network peer, so its defensive branches are the most important lines in the diff to prove. | test-reviewer | Accepted: bad-length, indefinite-length tests | Yes, and this is the best finding of the review. I tested the happy path with real certificates and the obvious junk, and skipped the branch that matters for hostile input. |
| 5 | Blocking | Two error branches in the time parser untested. | test-reviewer | Accepted, plus a direct test of both time encodings | Probably. |
| 6 | Should fix | The RDAP response body was read with no size cap. A misbehaving server could exhaust memory on the machine running the cron job. | security-reviewer | Accepted: 1 MB cap, refused with a message past that | Yes. |
| 7 | Should fix | Depending on `rdap.org`, a third-party redirector, is a boundary decision of the same weight as the no-verify choice that got ADR 0003, and it only had a docstring. | docs-reviewer | Accepted: ADR 0004 | Yes. I had made the decision carefully and not written it down, which is the exact failure ADR 0001 exists to stop. |
| 8 | Should fix | `--offline` is new user-facing surface not in the scope document. | scope-reviewer | Accepted: one line in scope, dated | No, but I would have skipped it. |
| 9 | Should fix | `test_unresolvable_host` did a real DNS lookup, against the scope rule that checker tests never touch the network. | test-reviewer | Accepted: injected `gaierror` | No. I knew and let it slide. The reviewer did not. |
| 10 | Handoff | Does the CI runner have `openssl`? If not, the real-handshake tests skip silently and coverage drops with no signal. | test-reviewer, docs-reviewer | Accepted: the tests now fail in CI (`CI=true`) when `openssl` is missing, and still skip locally | Yes. |
| 11 | Handoff | No review-log entry for this PR yet. | test-reviewer | No change needed: the entry is written after the review, which is this. | n/a |

**Totals:** 5 blocking, 4 should fix, 2 handoffs. 10 accepted, 0 deferred, 0 overridden, 1 no change needed. Would have missed: 6 of 10.

### Confirmed non-issues

security-reviewer reviewed the DER parser specifically as attacker-reachable input and found every read bounds-checked. security-reviewer and scope-reviewer both independently checked `CERT_NONE` against ADR 0003 and accepted it. docs-reviewer confirmed README, ADR 0003, and the checker code agree on timeouts, flags, fallback behavior, and exit codes.

### Overrides

None.

### What changed in the swarm because of this PR

Nothing in the charters. The roster fix from PR 1 held: scope-reviewer and test-reviewer both handed findings to real agents this time, and the merge step listed the two that nobody confirmed under "Handoffs nobody picked up" with the right names.

One thing in how the swarm was run. test-reviewer reported it could not execute the test suite because the harness did not grant it shell approval, and scope-reviewer reconstructed the diff from `.git/logs/HEAD` because it had no git access. Both said so plainly under Noted instead of pretending, which is what the contract asks. But a test reviewer that cannot run tests is reviewing with one eye shut. Next run gets an explicit tool allowlist so the agents can run `git`, `python`, and `uv`. That is a runner concern, tracked in the agentic-swarm repo.

### What the human did that the swarm did not

Chose the approach. The swarm cannot tell you that Python's `ssl` module refuses to hand back an expired certificate, or that the fix is forty lines of DER walking instead of a dependency. It can only tell you whether the forty lines are tested. It did.
