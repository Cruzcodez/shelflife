# Fixtures

Recorded responses so the tests never need the network.

- `valid.json`, `valid.yaml`: the same five-item inventory in both formats. Used everywhere.
- `rdap-example.com.json`: the real answer from `https://rdap.org/domain/example.com` (which redirects to Verisign's server), recorded 2026-09-14. The expiration event is the part the checker reads.
- `rdap-no-service.json`: the real 404 body `rdap.org` returns for a TLD that has no RDAP server (recorded against a `.de` domain, 2026-09-14). The checker turns this into a "track it with a manual date" message.

There is no recorded certificate on purpose. A certificate fixture would either be a real one that goes stale, or a self-signed one whose private key sits in the repo and trips every secret scanner including our own. Instead `tests/test_tls.py` generates a throwaway certificate with `openssl` at test time, serves it from a local TLS server, and runs the real checker against that. If `openssl` is not on the PATH those tests skip and say so.
