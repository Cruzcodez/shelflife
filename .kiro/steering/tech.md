# Tech constraints

## Stack

- **Language:** Python 3.11 or newer
- **Runtime / platform:** any machine with Python and a network connection. Cron for scheduling.
- **IaC:** none
- **Test framework:** pytest, with recorded network responses so tests run offline
- **Package manager:** uv, with a lockfile

## Allowed

Standard library for everything it can do: `ssl`, `socket`, `datetime`, `json`, `argparse`, `urllib`. PyYAML for the inventory. `httpx` for RDAP if `urllib` gets painful. pytest and ruff for checks.

## Requires approval

Any other runtime dependency. Say in the PR why the standard library wasn't enough.

## Forbidden

- Storing a certificate private key, an API key value, a password, or any secret in the inventory, the code, the tests, or the repo. The inventory holds names and dates. This is the whole security model and the security reviewer blocks on it.
- Any code path that renews, rotates, or modifies the thing being tracked. This tool reads.
- Cloud SDKs in the core. Integrations are a separate module, later, if ever.
- Tests that hit the real network. Record the response once, replay it in the test.

## Cloud

None required. Nothing here deploys anywhere.
