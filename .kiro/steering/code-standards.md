# Code standards

Applies to everything in this repository, written by a human or an agent.

## Size

Small is the default. A proof of concept that solves the problem in 300 lines is a better deliverable than one that solves it in 3,000 with room to grow. Build for the requirement in front of you, not the one you imagine arriving.

Delete dead code rather than commenting it out.

## Structure

- One concern per file. If you can't name the file after what it does, it does too much.
- Configuration comes from the environment, never from hardcoded values.
- No resource identifiers in source: no account IDs, bucket names, distribution IDs, endpoints, pool IDs.
- Prefer boring, explicit code over clever code. The reader may not be you.

## Errors

Fail loudly and early. Silent fallbacks hide bugs until they're expensive.

Error messages say what went wrong *and* what to do about it.

## Tests

A test exists to fail when behavior breaks. A test that can't fail is decoration.

Cover the path the user actually takes and the failure modes you know about. Don't chase a coverage percentage on a POC.

## Dependencies

Every dependency is permanent maintenance and supply-chain surface. Prefer the standard library. Justify additions in the PR.

## Documentation

The README is part of the deliverable, not an afterthought. If someone can't tell what this does, why it exists, how to run it, and what its limits are, the work isn't finished — regardless of whether the code runs.
