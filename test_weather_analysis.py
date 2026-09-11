import io
import unittest

import pandas as pd

from weather_analysis import (
    coldest_month,
    heatwave_days_per_year,
    hottest_month,
    load_data,
    monthly_climatology,
    trend_slope,
    yearly_trend,
)


def make_test_df():
    """A tiny 2-year, 2-month synthetic dataset with a known, exact
    +2 degree/year warming trend and one deliberate heatwave day, so the
    expected results can be computed by hand."""
    rows = []
    # Year 1 (2020): January cool, July hot, no heatwave.
    for day in range(1, 6):
        rows.append({"date": f"2020-01-{day:02d}", "temp_max_c": 15.0, "temp_min_c": 8.0})
        rows.append({"date": f"2020-07-{day:02d}", "temp_max_c": 35.0, "temp_min_c": 22.0})
    # Year 2 (2021): every value +2 degrees, plus one heatwave day in July.
    for day in range(1, 6):
        rows.append({"date": f"2021-01-{day:02d}", "temp_max_c": 17.0, "temp_min_c": 10.0})
        rows.append({"date": f"2021-07-{day:02d}", "temp_max_c": 37.0, "temp_min_c": 24.0})
    rows.append({"date": "2021-07-06", "temp_max_c": 42.0, "temp_min_c": 25.0})

    csv_text = "date,temp_max_c,temp_min_c\n" + "\n".join(
        f"{r['date']},{r['temp_max_c']},{r['temp_min_c']}" for r in rows
    )
    df = pd.read_csv(io.StringIO(csv_text), parse_dates=["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


class TestYearlyTrend(unittest.TestCase):
    def test_yearly_trend_averages_by_year(self):
        df = make_test_df()
        yearly = yearly_trend(df)
        # 2020: (15*5 + 35*5)/10 = 25.0 ; 2021: (17*5 + 37*5 + 42)/11
        self.assertAlmostEqual(yearly[2020], 25.0)
        self.assertAlmostEqual(yearly[2021], (17 * 5 + 37 * 5 + 42) / 11, places=3)

    def test_trend_slope_is_positive_for_warming_data(self):
        df = make_test_df()
        slope = trend_slope(df)
        self.assertGreater(slope, 0)

    def test_trend_slope_is_zero_with_a_single_year(self):
        df = make_test_df()
        single_year = df[df["year"] == 2020]
        self.assertEqual(trend_slope(single_year), 0.0)


class TestSeasonalProfile(unittest.TestCase):
    def test_monthly_climatology_separates_hot_and_cold_months(self):
        df = make_test_df()
        climatology = monthly_climatology(df)
        self.assertLess(climatology.loc[1, "temp_max_c"], climatology.loc[7, "temp_max_c"])

    def test_hottest_and_coldest_month_are_correctly_identified(self):
        df = make_test_df()
        hot_month, hot_temp = hottest_month(df)
        cold_month, cold_temp = coldest_month(df)
        self.assertEqual(hot_month, "Jul")
        self.assertEqual(cold_month, "Jan")
        self.assertGreater(hot_temp, cold_temp)

    def test_climatology_only_has_rows_for_months_present_in_data(self):
        df = make_test_df()
        climatology = monthly_climatology(df)
        # Months with no data (e.g. March) should be NaN, not missing/zero.
        self.assertTrue(pd.isna(climatology.loc[3, "temp_max_c"]))


class TestHeatwaveDays(unittest.TestCase):
    def test_heatwave_count_matches_the_one_planted_hot_day(self):
        df = make_test_df()
        counts = heatwave_days_per_year(df, threshold=40.0)
        self.assertEqual(counts[2020], 0)
        self.assertEqual(counts[2021], 1)

    def test_all_years_appear_even_with_zero_heatwaves(self):
        df = make_test_df()
        counts = heatwave_days_per_year(df, threshold=100.0)
        self.assertEqual(list(counts.index), [2020, 2021])
        self.assertEqual(counts[2020], 0)
        self.assertEqual(counts[2021], 0)


class TestLoadData(unittest.TestCase):
    def test_load_data_adds_year_and_month_columns(self):
        df = load_data("data/cairo_temperatures.csv")
        self.assertIn("year", df.columns)
        self.assertIn("month", df.columns)
        self.assertGreater(len(df), 1000)


if __name__ == "__main__":
    unittest.main()
