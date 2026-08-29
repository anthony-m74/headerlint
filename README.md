# headerlint

A small library and CLI for parsing raw HTTP header text and checking it
for common mistakes - duplicate headers that should be unique, missing
security headers, and so on.

The use case: you've got a blob of headers from `curl -I`, a browser
devtools "copy request headers" action, or a line pulled out of a log
file, and you want to know if anything looks wrong without eyeballing
it. `headerlint` parses that blob and runs a handful of checks against
it.

## Install

No dependencies, standard library only. Clone the repo and run it
in place, or install it locally:

```
pip install -e .
```

## Usage

From a file:

```
$ headerlint response.txt
[warning] 'content-type' appears 2 times but should be unique
[info] missing recommended security header: strict-transport-security
```

From stdin, which is the more common case in practice:

```
$ curl -sI https://example.com | headerlint
3 headers, no problems found
```

`-` also works as an explicit way to say "read from stdin":

```
$ cat headers.txt | headerlint -
```

Use `--list` to just see the parsed headers, one per line, without
running any checks:

```
$ headerlint --list response.txt
Content-Type: text/html; charset=utf-8
Cache-Control: no-cache
```

## As a library

```python
from headerlint import parse_headers, run_all_checks

text = """\
HTTP/1.1 200 OK
Content-Type: text/html
Content-Type: text/plain
"""

headers = parse_headers(text)
for finding in run_all_checks(headers):
    print(finding.level, finding.message)
```

`parse_headers` skips a leading request or status line if one is
present, and folds obsolete line-continuation headers (a line starting
with whitespace) onto the previous header's value.

## Exit status

`headerlint` exits 0 when parsing succeeds and no checks fail, and 1
otherwise - both for parse errors and for findings, so it's usable as
a CI gate.
