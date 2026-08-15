import unittest

from tests.smoke.run_live import assert_browser_fingerprint, normalize_browser


class SmokeBrowserTests(unittest.TestCase):
    def test_normalize(self) -> None:
        self.assertEqual(normalize_browser("edge"), "msedge")
        self.assertEqual(normalize_browser("msedge"), "msedge")
        self.assertEqual(normalize_browser("chrome"), "chromium")

    def test_accepts_edge_ua(self) -> None:
        assert_browser_fingerprint(
            "msedge",
            "Mozilla/5.0 ... Chrome/141.0.0.0 Safari/537.36 Edg/141.0.3537.92",
            ["Microsoft Edge", "Chromium", "Not-A.Brand"],
        )

    def test_rejects_chromium_when_edge_requested(self) -> None:
        with self.assertRaises(SystemExit):
            assert_browser_fingerprint(
                "msedge",
                "Mozilla/5.0 ... Chrome/141.0.0.0 Safari/537.36",
                ["Chromium", "Not-A.Brand"],
            )


if __name__ == "__main__":
    unittest.main()
