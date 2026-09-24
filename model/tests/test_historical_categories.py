import unittest

from vicforecast.polling.historical_categories import translate_poll_categories


class HistoricalCategoryTests(unittest.TestCase):
    def test_active_five_family_poll_keeps_explicit_shares(self):
        result = translate_poll_categories(
            "vic_la_2022",
            ("ALP", "Coalition", "Greens", "One Nation", "Other/Independent"),
            {"ALP": 35, "Coalition": 38, "Greens": 10, "One Nation": 12, "Other": 5},
        )
        self.assertEqual(result.explicit_shares["One Nation"], 12)
        self.assertEqual(result.residual_share, 5)
        self.assertEqual(result.reported_but_unavailable, ())

    def test_inactive_family_is_not_invented_as_zero(self):
        result = translate_poll_categories(
            "vic_la_2018",
            ("ALP", "Coalition", "Greens", "Other/Independent"),
            {"ALP": 40, "Coalition": 40, "Greens": 11, "Other": 9},
        )
        self.assertNotIn("One Nation", result.explicit_shares)
        self.assertEqual(result.residual_share, 9)

    def test_reported_but_unavailable_family_is_diagnostic(self):
        result = translate_poll_categories(
            "vic_la_2018",
            ("ALP", "Coalition", "Greens", "Other/Independent"),
            {"ALP": 40, "Coalition": 40, "Greens": 11, "One Nation": 2, "Other": 7},
        )
        self.assertEqual(result.reported_but_unavailable, ("One Nation",))
        self.assertNotIn("One Nation", result.explicit_shares)


if __name__ == "__main__":
    unittest.main()
