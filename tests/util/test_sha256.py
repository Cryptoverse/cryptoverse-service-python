from unittest import TestCase


class TestSha256(TestCase):
    def test_sha256(self):
        from project import util
        testres = util.sha256("message")
        assert testres.lower() == "AB530A13E45914982B79F9B7E3FBA994" \
                                  "CFD1F3FB22F71CEA1AFBF02B460C6D1D".lower()
