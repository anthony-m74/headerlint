"""Checks that flag common problems in a parsed header set.

These are deliberately conservative - each one is something that is
almost always a mistake, not a style opinion. Header names are matched
case-insensitively, since HTTP header names are case-insensitive by
spec (RFC 7230 section 3.2).
"""

from __future__ import annotations

from dataclasses import dataclass

from .parser import Header

# Headers that browsers and proxies treat specially if duplicated -
# having more than one is a bug, not a choice, unlike e.g. Set-Cookie
# or Link which are fine to repeat.
_SINGLE_VALUE_ONLY = (
    "content-type",
    "content-length",
    "host",
    "location",
)

_RECOMMENDED_SECURITY_HEADERS = (
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
    "content-security-policy",
)


@dataclass(frozen=True)
class Finding:
    level: str  # "warning" or "info"
    message: str


def find_duplicates(headers: list[Header]) -> list[Finding]:
    counts: dict[str, int] = {}
    for h in headers:
        key = h.name.lower()
        counts[key] = counts.get(key, 0) + 1

    return [
        Finding("warning", f"'{key}' appears {count} times but should be unique")
        for key, count in counts.items()
        if count > 1 and key in _SINGLE_VALUE_ONLY
    ]


def find_missing_security_headers(headers: list[Header]) -> list[Finding]:
    present = {h.name.lower() for h in headers}
    return [
        Finding("info", f"missing recommended security header: {name}")
        for name in _RECOMMENDED_SECURITY_HEADERS
        if name not in present
    ]


def run_all_checks(headers: list[Header]) -> list[Finding]:
    return find_duplicates(headers) + find_missing_security_headers(headers)
