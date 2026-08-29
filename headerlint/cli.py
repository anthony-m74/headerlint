"""The `headerlint` command: read headers from a file or stdin, report."""

from __future__ import annotations

import argparse
import sys

from .checks import run_all_checks
from .parser import ParseError, parse_headers


def _read_input(path: str | None) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="headerlint",
        description="Parse and check raw HTTP headers for common problems.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help="file containing raw headers (default: stdin; pass '-' to be explicit)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print the parsed headers instead of running checks",
    )
    args = parser.parse_args(argv)

    try:
        text = _read_input(args.file)
    except OSError as exc:
        print(f"headerlint: {exc}", file=sys.stderr)
        return 1

    try:
        headers = parse_headers(text)
    except ParseError as exc:
        print(f"headerlint: {exc}", file=sys.stderr)
        return 1

    if not headers:
        print("headerlint: no headers found in input", file=sys.stderr)
        return 1

    if args.list:
        for h in headers:
            print(h)
        return 0

    findings = run_all_checks(headers)
    if not findings:
        print(f"{len(headers)} headers, no problems found")
        return 0

    for finding in findings:
        print(f"[{finding.level}] {finding.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
