import unittest
from datetime import date

from usuarios.services.weather_service import WeatherService


class RainHistorySummaryTests(unittest.TestCase):
    def setUp(self):
        self.service = WeatherService()

    def test_deduplicates_days_and_keeps_zero_separate_from_missing(self):
        observations = [
            {"obsTimeLocal": "2026-09-01 23:59:00", "metric": {"precipTotal": 2.5}},
            {"obsTimeLocal": "2026-09-01 23:59:01", "metric": {"precipTotal": 9.0}},
            {"obsTimeLocal": "2026-09-02 23:59:00", "metric": {"precipTotal": 0.0}},
            {"obsTimeLocal": "2026-09-03 23:59:00", "metric": {"precipTotal": None}},
        ]

        result = self.service._summarize_rain_history(
            observations,
            2026,
            date(2026, 9, 3),
        )

        september = result["months"][8]
        self.assertEqual(september["total_mm"], 2.5)
        self.assertEqual(september["available_days"], 2)
        self.assertEqual(september["expected_days"], 3)
        self.assertEqual(september["status"], "partial")
        self.assertEqual(september["missing_days"], ["2026-09-03"])
        self.assertEqual(result["annual_total_mm"], 2.5)
        self.assertTrue(result["incomplete"])

    def test_unavailable_days_do_not_become_zero_precipitation(self):
        result = self.service._summarize_rain_history(
            [],
            2026,
            date(2026, 1, 2),
        )

        self.assertIsNone(result["annual_total_mm"])
        self.assertIsNone(result["months"][0]["total_mm"])
        self.assertEqual(result["months"][0]["status"], "unavailable")

    def test_leap_day_is_included_in_expected_coverage(self):
        result = self.service._summarize_rain_history(
            [{"obsTimeLocal": "2024-02-29 23:59:00", "metric": {"precipTotal": 0.0}}],
            2024,
            date(2024, 2, 29),
        )

        february = result["months"][1]
        self.assertEqual(february["expected_days"], 29)
        self.assertEqual(february["available_days"], 1)
        self.assertEqual(february["total_mm"], 0.0)