"""Live checkers, one per live item type.

A checker is a function that takes an Item and returns the expiry date it found. It raises on
any failure and `report.evaluate` turns that into an error line for that one item. See
`report.py` for the contract and `docs/decisions/0002-exit-codes.md` for what an error means
to the exit code.
"""

from .rdap import rdap_expiry
from .tls import tls_expiry

CHECKERS = {
    "tls": tls_expiry,
    "domain": rdap_expiry,
}

__all__ = ["CHECKERS", "rdap_expiry", "tls_expiry"]
