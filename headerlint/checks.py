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

# (display name, attribute name as it appears lowercased in Set-Cookie)
_COOKIE_SECURITY_FLAGS = (
    ("Secure", "secure"),
    ("HttpOnly", "httponly"),
    ("SameSite", "samesite"),
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


def find_insecure_cookies(headers: list[Header]) -> list[Finding]:
    """Flag Set-Cookie headers missing Secure, HttpOnly, or SameSite.

    Cookies without these get sent over plain HTTP, read by page
    scripts, or attached to cross-site requests - each is a narrower
    hole than the one before, but all three are cheap to close.
    """
    findings = []
    for h in headers:
        if h.name.lower() != "set-cookie":
            continue

        attrs = [a.strip() for a in h.value.split(";")]
        cookie_pair, *attrs = attrs
        if "=" not in cookie_pair:
            continue
        cookie_name = cookie_pair.split("=", 1)[0].strip()
        if not cookie_name:
            continue

        present = {a.split("=", 1)[0].strip().lower() for a in attrs if a}
        missing = [flag for flag, key in _COOKIE_SECURITY_FLAGS if key not in present]
        if missing:
            findings.append(
                Finding("warning", f"cookie '{cookie_name}' is missing {', '.join(missing)}")
            )

    return findings


def run_all_checks(headers: list[Header]) -> list[Finding]:
    return (
        find_duplicates(headers)
        + find_missing_security_headers(headers)
        + find_insecure_cookies(headers)
    )
