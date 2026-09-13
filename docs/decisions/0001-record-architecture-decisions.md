# 1. Record architecture decisions

**Status:** Accepted
**Date:** YYYY-MM-DD

## Context

Six months from now, someone — possibly me, possibly a customer engineering team inheriting this — will look at a piece of this system and ask "why is it like that?"

Code records *what* was decided. It does not record what else was considered, what constraint forced the choice, or what would have to change for the decision to be revisited. That information is currently only in my head and in a chat log, and both of those are gone by then.

## Decision

Every decision that constrains future work gets a short record in `docs/decisions/`, numbered sequentially, using this format: Context, Decision, Consequences.

A decision qualifies if reversing it later would be expensive — choice of datastore, auth model, deployment target, a boundary between components, a deliberate omission.

It does not qualify if it's a preference with no downstream cost. Naming conventions and formatting go in steering docs, not here.

## Consequences

- A reviewer can reconstruct the reasoning without asking me.
- A handoff includes the *why*, which is most of what makes a repository usable by someone else.
- Small ongoing cost: roughly ten minutes per real decision.
- Records are immutable. A decision that changes gets a new ADR that supersedes the old one; the old one stays, marked Superseded. The history of the reasoning is the point.

---

Copy this file as a template. Keep them short — if an ADR runs past a page, the decision probably isn't as settled as you think.
