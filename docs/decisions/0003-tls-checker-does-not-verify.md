# 3. The TLS checker reads the certificate without verifying it

**Status:** Accepted
**Date:** 2026-09-14

## Context

The TLS checker connects to a host, completes the handshake, and reads the expiry date off the certificate the server presents. The obvious way to write that in Python is `ssl.create_default_context()`, which verifies the certificate chain and the hostname, and then `getpeercert()`, which returns the parsed certificate.

That combination fails on exactly the certificates this tool exists to find. An expired certificate does not pass verification, so the handshake is refused and the parsed certificate is never available. The tool would report "error: certificate verify failed" for an item whose correct status is "expired 3 days ago." A self-signed certificate on an internal host, which is a normal thing to want to track, fails the same way.

Verification also fails when the hostname does not match, which happens when the inventory points at an IP address or an internal name that is not on the certificate. Again, the date is what we want and it is right there.

## Decision

The checker builds its own `SSLContext` with `check_hostname = False` and `verify_mode = CERT_NONE`, sends SNI so virtual hosts answer with the right certificate, takes the certificate in raw DER form with `getpeercert(binary_form=True)`, and reads `notAfter` with a small purpose-built parser in `src/expiry_tracker/x509.py`.

Nothing is sent or received over the connection after the handshake. The tool closes the socket as soon as it has the certificate bytes.

## Why this is safe

Verification protects data that flows over a connection. This connection carries no data. A man in the middle who presents a fake certificate can make the tool report a wrong expiry date for that one item, and nothing else. The blast radius is one line in a report, and the operator sees a date that disagrees with what their browser shows.

## Consequences

- Expired, self-signed, and hostname-mismatched certificates all report their real expiry date, which is the behavior an inventory tool needs.
- The tool cannot tell you whether a certificate is trusted, only when it expires. That is the scope. Trust checking is a different tool.
- A security reviewer reading `CERT_NONE` will flag it. That is a good instinct and this document is the answer. The code comment points here.
- `src/expiry_tracker/x509.py` exists because Python's standard library has no certificate parser for the unverified case. It reads one field and refuses anything it does not understand. If it ever needs to read a second field, that is the moment to consider a real dependency such as `cryptography` instead of growing it.
