import unittest

from headerlint.parser import Header, ParseError, parse_headers


class ParseHeadersTests(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(parse_headers(""), [])

    def test_blank_lines_only(self):
        self.assertEqual(parse_headers("\n\n   \n\t\n"), [])

    def test_basic_headers_no_request_or_status_line(self):
        text = "Content-Type: text/html\nCache-Control: no-cache\n"
        self.assertEqual(
            parse_headers(text),
            [Header("Content-Type", "text/html"), Header("Cache-Control", "no-cache")],
        )

    def test_skips_leading_status_line(self):
        text = "HTTP/1.1 200 OK\nContent-Type: text/html\n"
        self.assertEqual(parse_headers(text), [Header("Content-Type", "text/html")])

    def test_skips_leading_status_line_http2(self):
        text = "HTTP/2 200\nContent-Type: text/html\n"
        self.assertEqual(parse_headers(text), [Header("Content-Type", "text/html")])

    def test_skips_leading_request_line(self):
        text = "GET /index.html HTTP/1.1\nHost: example.com\n"
        self.assertEqual(parse_headers(text), [Header("Host", "example.com")])

    def test_blank_lines_between_headers_are_ignored(self):
        text = "Content-Type: text/html\n\nCache-Control: no-cache\n"
        self.assertEqual(
            parse_headers(text),
            [Header("Content-Type", "text/html"), Header("Cache-Control", "no-cache")],
        )

    def test_name_and_value_are_stripped(self):
        text = "  Content-Type  :   text/html  \n"
        self.assertEqual(parse_headers(text), [Header("Content-Type", "text/html")])

    def test_value_may_contain_colons(self):
        text = "Location: https://example.com:8443/path\n"
        self.assertEqual(
            parse_headers(text),
            [Header("Location", "https://example.com:8443/path")],
        )

    def test_value_may_be_empty(self):
        text = "X-Empty:\n"
        self.assertEqual(parse_headers(text), [Header("X-Empty", "")])

    def test_continuation_line_is_folded_onto_previous_value(self):
        text = "X-Long: part one\n part two\n"
        self.assertEqual(parse_headers(text), [Header("X-Long", "part one part two")])

    def test_continuation_line_with_tab_indent(self):
        text = "X-Long: part one\n\tpart two\n"
        self.assertEqual(parse_headers(text), [Header("X-Long", "part one part two")])

    def test_continuation_with_no_preceding_header_raises(self):
        with self.assertRaises(ParseError):
            parse_headers(" leading whitespace with nothing before it\n")

    def test_line_without_colon_raises(self):
        with self.assertRaises(ParseError):
            parse_headers("Content-Type: text/html\nthis has no colon\n")

    def test_empty_header_name_raises(self):
        with self.assertRaises(ParseError):
            parse_headers(": value with no name\n")

    def test_duplicate_headers_are_preserved_in_order(self):
        text = "Set-Cookie: a=1\nSet-Cookie: b=2\n"
        self.assertEqual(
            parse_headers(text),
            [Header("Set-Cookie", "a=1"), Header("Set-Cookie", "b=2")],
        )

    def test_crlf_line_endings(self):
        text = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nX-Test: value\r\n"
        self.assertEqual(
            parse_headers(text),
            [Header("Content-Type", "text/html"), Header("X-Test", "value")],
        )

    def test_header_str_round_trips(self):
        h = Header("Content-Type", "text/html")
        self.assertEqual(str(h), "Content-Type: text/html")


if __name__ == "__main__":
    unittest.main()
