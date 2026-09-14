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
