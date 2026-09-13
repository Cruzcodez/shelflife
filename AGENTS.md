# Agent instructions

Read this before making changes. It applies to Claude, Kiro, and any other coding agent working in this repository.

## Working agreement

- **No code before requirements.** If the task isn't written down in `docs/` or an issue, write it down first and confirm it. A prompt is not a requirement.
- **Smallest change that works.** Prefer 30 lines that solve the problem over 300 that anticipate problems nobody has.
- **One concern per commit.** If the commit message needs the word "and", it's two commits.
- **Ask before adding a dependency.** Every dependency is a permanent maintenance obligation and a supply-chain surface.
- **Never invent scope.** If you notice something else worth fixing, say so and leave it alone.

## Definition of done

A change is not done until all of these are true:

- [ ] It does what the requirement said, and nothing the requirement didn't say
- [ ] `./scripts/check.sh` passes
- [ ] New behavior has a test that fails without the change
- [ ] No secrets, credentials, live endpoints, or real customer data added to tracked files
- [ ] README updated if behavior, setup, or limitations changed
- [ ] A decision that constrains future work is recorded as an ADR in `docs/decisions/`

## Commits

Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`.

Subject line under 72 characters, imperative mood, describes the change not the file touched. Body explains *why* when the reason isn't obvious from the diff.

## What not to do

- Don't commit `.env` files. Check `.gitignore` covers the naming you actually used, not just `.env`.
- Don't hardcode endpoints, account IDs, bucket names, or resource identifiers.
- Don't create documentation files nobody asked for. One README, one CHANGELOG, ADRs as needed.
- Don't refactor code you weren't asked to touch.
- Don't leave commented-out code. Git remembers it.

## Security

Anything that would be a credential if it were real is treated as a credential. If you are unsure whether a value is sensitive, assume it is and ask.
