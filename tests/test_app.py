"""Tests for the local HTTP server's pure request helpers."""

import unittest

from app import extract_bearer_token


class ExtractBearerTokenTests(unittest.TestCase):
    def test_extracts_bearer_credential(self):
        self.assertEqual(extract_bearer_token("Bearer secret"), "secret")

    def test_scheme_is_case_insensitive(self):
        self.assertEqual(extract_bearer_token("bearer secret"), "secret")

    def test_ignores_missing_or_blank_credentials(self):
        self.assertIsNone(extract_bearer_token(None))
        self.assertIsNone(extract_bearer_token(""))
        self.assertIsNone(extract_bearer_token("Bearer   "))

    def test_rejects_other_authorization_schemes(self):
        self.assertIsNone(extract_bearer_token("Basic secret"))


if __name__ == "__main__":
    unittest.main()
