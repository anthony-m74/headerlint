import unittest

from headerlint.checks import find_insecure_cookies
from headerlint.parser import Header


class FindInsecureCookiesTests(unittest.TestCase):
    def test_cookie_with_all_flags_is_fine(self):
        h = Header("Set-Cookie", "session=abc; Secure; HttpOnly; SameSite=Strict")
        self.assertEqual(find_insecure_cookies([h]), [])

    def test_flags_are_case_insensitive(self):
        h = Header("Set-Cookie", "session=abc; secure; httponly; samesite=lax")
        self.assertEqual(find_insecure_cookies([h]), [])

    def test_missing_all_flags(self):
        h = Header("Set-Cookie", "session=abc")
        findings = find_insecure_cookies([h])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].level, "warning")
        self.assertIn("session", findings[0].message)
        self.assertIn("Secure", findings[0].message)
        self.assertIn("HttpOnly", findings[0].message)
        self.assertIn("SameSite", findings[0].message)

    def test_missing_one_flag_is_named(self):
        h = Header("Set-Cookie", "session=abc; HttpOnly; SameSite=Strict")
        findings = find_insecure_cookies([h])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].message, "cookie 'session' is missing Secure")

    def test_header_name_is_matched_case_insensitively(self):
        h = Header("set-cookie", "session=abc")
        self.assertEqual(len(find_insecure_cookies([h])), 1)

    def test_multiple_set_cookie_headers_are_checked_independently(self):
        headers = [
            Header("Set-Cookie", "a=1; Secure; HttpOnly; SameSite=Strict"),
            Header("Set-Cookie", "b=2"),
        ]
        findings = find_insecure_cookies(headers)
        self.assertEqual(len(findings), 1)
        self.assertIn("'b'", findings[0].message)

    def test_non_cookie_headers_are_ignored(self):
        h = Header("Content-Type", "text/html")
        self.assertEqual(find_insecure_cookies([h]), [])

    def test_cookie_with_no_equals_sign_is_ignored(self):
        h = Header("Set-Cookie", "not-a-valid-cookie")
        self.assertEqual(find_insecure_cookies([h]), [])

    def test_attribute_values_do_not_confuse_flag_detection(self):
        # "Path=/" and "Max-Age=3600" have their own "=" and must not be
        # mistaken for Secure/HttpOnly/SameSite.
        h = Header("Set-Cookie", "session=abc; Path=/; Max-Age=3600")
        findings = find_insecure_cookies([h])
        self.assertEqual(len(findings), 1)
        self.assertEqual(
            findings[0].message, "cookie 'session' is missing Secure, HttpOnly, SameSite"
        )


if __name__ == "__main__":
    unittest.main()
