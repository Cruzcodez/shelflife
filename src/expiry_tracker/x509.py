"""Read the expiry date out of a raw DER-encoded X.509 certificate.

Why this exists: Python's `ssl` module only returns a parsed certificate when it verified the
chain. A certificate that has already expired fails verification, so the parsed form is empty
exactly when we most need the date. The raw bytes are always available, so we read them.

This is not a general certificate parser. It walks the ASN.1 structure far enough to reach the
Validity field and stops. Everything it needs is fixed by RFC 5280 section 4.1:

    Certificate ::= SEQUENCE {
        tbsCertificate ::= SEQUENCE {
            version    [0] EXPLICIT INTEGER OPTIONAL,
            serialNumber        INTEGER,
            signature           SEQUENCE,
            issuer              SEQUENCE,
            validity ::= SEQUENCE { notBefore Time, notAfter Time },
            ...
"""

from __future__ import annotations

from datetime import UTC, date, datetime

_TAG_SEQUENCE = 0x30
_TAG_UTC_TIME = 0x17
_TAG_GENERALIZED_TIME = 0x18
_TAG_VERSION = 0xA0  # context-specific [0], constructed


class CertificateError(ValueError):
    """The bytes are not a certificate this module can read."""


def not_after(der: bytes) -> date:
    """Return the notAfter date of a DER-encoded certificate."""
    _, tbs = _expect(der, 0, _TAG_SEQUENCE)  # Certificate
    _, body = _expect(tbs, 0, _TAG_SEQUENCE)  # tbsCertificate
    pos = 0
    if body[pos : pos + 1] == bytes([_TAG_VERSION]):
        _, _, pos = _read(body, pos)  # version, only present for v2 and v3
    _, _, pos = _read(body, pos)  # serialNumber
    _, _, pos = _read(body, pos)  # signature algorithm
    _, _, pos = _read(body, pos)  # issuer
    _, validity = _expect(body, pos, _TAG_SEQUENCE)
    _, _, pos = _read(validity, 0)  # notBefore
    tag, value, _ = _read(validity, pos)  # notAfter
    return _parse_time(tag, value).date()


def _read(buf: bytes, pos: int) -> tuple[int, bytes, int]:
    """Read one TLV at pos. Returns (tag, value bytes, position after it)."""
    if pos >= len(buf):
        raise CertificateError("certificate is truncated")
    tag = buf[pos]
    pos += 1
    if pos >= len(buf):
        raise CertificateError("certificate is truncated")
    first = buf[pos]
    pos += 1
    if first < 0x80:
        length = first
    else:
        n = first & 0x7F
        if n == 0 or n > 4 or pos + n > len(buf):
            raise CertificateError("bad length encoding")
        length = int.from_bytes(buf[pos : pos + n], "big")
        pos += n
    end = pos + length
    if end > len(buf):
        raise CertificateError("certificate is truncated")
    return tag, buf[pos:end], end


def _expect(buf: bytes, pos: int, tag: int) -> tuple[int, bytes]:
    got, value, end = _read(buf, pos)
    if got != tag:
        raise CertificateError(f"expected tag 0x{tag:02x} at offset {pos}, got 0x{got:02x}")
    return end, value


def _parse_time(tag: int, value: bytes) -> datetime:
    text = value.decode("ascii", errors="replace")
    if tag == _TAG_UTC_TIME:
        # YYMMDDHHMMSSZ. RFC 5280 requires anything from 2050 on to use GeneralizedTime, so the
        # two-digit year is never ambiguous in a valid certificate.
        fmt = "%y%m%d%H%M%SZ"
    elif tag == _TAG_GENERALIZED_TIME:
        fmt = "%Y%m%d%H%M%SZ"
    else:
        raise CertificateError(f"unexpected time tag 0x{tag:02x} where notAfter should be")
    try:
        return datetime.strptime(text, fmt).replace(tzinfo=UTC)
    except ValueError as e:
        raise CertificateError(f"unreadable notAfter {text!r}") from e
