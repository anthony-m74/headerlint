"""Turn raw HTTP header text into a list of Header objects.

The input is whatever you can copy out of `curl -I`, browser devtools,
or a log line: an optional request or status line, then one
"Name: Value" pair per line. That's easier to get right than it sounds
because real-world dumps disagree on line endings, leading/trailing
whitespace, and whether the first line is even a header at all.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_REQUEST_LINE = re.compile(r"^[A-Z]+ \S+ HTTP/\d(\.\d)?$")
_STATUS_LINE = re.compile(r"^HTTP/\d(\.\d)?\s+\d{3}")


@dataclass(frozen=True)
class Header:
    name: str
    value: str

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"


class ParseError(ValueError):
    pass


def parse_headers(text: str) -> list[Header]:
    """Parse raw header text into a list of Header objects, in order.

    A leading request line ("GET / HTTP/1.1") or status line
    ("HTTP/1.1 200 OK") is skipped if present. A continuation line
    (one starting with whitespace) is folded onto the previous
    header's value, per RFC 7230 section 3.2.4 - obsolete, but still
    something real servers emit.
    """
    headers: list[Header] = []

    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue

        if raw_line[0] in (" ", "\t"):
            if not headers:
                raise ParseError(f"continuation line with no preceding header: {raw_line!r}")
            prev = headers[-1]
            headers[-1] = Header(prev.name, prev.value + " " + raw_line.strip())
            continue

        if _REQUEST_LINE.match(raw_line) or _STATUS_LINE.match(raw_line):
            continue

        if ":" not in raw_line:
            raise ParseError(f"line has no colon and isn't a request/status line: {raw_line!r}")

        name, _, value = raw_line.partition(":")
        name = name.strip()
        value = value.strip()
        if not name:
            raise ParseError(f"empty header name: {raw_line!r}")

        headers.append(Header(name, value))

    return headers
