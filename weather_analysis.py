"""
Cairo Weather Trend Analysis — a "weather trend analysis" backlog item
localized to Cairo: multi-year warming trend, monthly seasonal profile,
and heatwave-day counts, built on a synthetic-but-climate-realistic daily
temperature record (see generate_data.py for why it's synthetic and how
it's built).
"""

import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def load_data(path):
    df = pd.read_csv(path, parse_dates=["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df


def yearly_trend(df, column="temp_max_c"):
    """Mean value of `column` per calendar year."""
    return df.groupby("year")[column].mean()


def trend_slope(df, column="temp_max_c"):
    """Degrees per year, from a simple linear fit of yearly means against
    year number — the headline "is it warming" number."""
    yearly = yearly_trend(df, column)
    if len(yearly) < 2:
        return 0.0
    slope, _intercept = np.polyfit(yearly.index.to_numpy(dtype=float), yearly.to_numpy(), 1)
    return float(slope)


def monthly_climatology(df):
    """Average high/low per calendar month, across all years — Cairo's
    'typical year' seasonal shape."""
    result = df.groupby("month")[["temp_max_c", "temp_min_c"]].mean()
    return result.reindex(range(1, 13))


def hottest_month(df):
    climatology = monthly_climatology(df)
    month_num = climatology["temp_max_c"].idxmax()
    return MONTH_NAMES[month_num - 1], climatology.loc[month_num, "temp_max_c"]


def coldest_month(df):
    climatology = monthly_climatology(df)
    month_num = climatology["temp_max_c"].idxmin()
    return MONTH_NAMES[month_num - 1], climatology.loc[month_num, "temp_max_c"]


def heatwave_days_per_year(df, threshold=40.0):
    """Count of days per year where temp_max_c exceeded `threshold`."""
    hot = df[df["temp_max_c"] > threshold]
    counts = hot.groupby("year").size()
    return counts.reindex(sorted(df["year"].unique()), fill_value=0)


def plot_yearly_trend(df, output_path, column="temp_max_c"):
    yearly = yearly_trend(df, column)
    slope = trend_slope(df, column)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(yearly.index, yearly.values, marker="o", color="#c0392b", linewidth=2)
    ax.set_title(f"Cairo yearly average {column} ({slope:+.2f}°C/year)")
    ax.set_xlabel("Year")
    ax.set_ylabel("°C")
    ax.set_xticks(list(yearly.index))
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


def plot_seasonal_profile(df, output_path):
    climatology = monthly_climatology(df)

    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(1, 13)
    ax.plot(x, climatology["temp_max_c"], marker="o", label="Avg high", color="#e67e22")
    ax.plot(x, climatology["temp_min_c"], marker="o", label="Avg low", color="#2980b9")
    ax.fill_between(x, climatology["temp_min_c"], climatology["temp_max_c"], alpha=0.15, color="#e67e22")
    ax.set_xticks(list(x))
    ax.set_xticklabels(MONTH_NAMES)
    ax.set_title("Cairo seasonal temperature profile")
    ax.set_ylabel("°C")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Cairo Weather Trend Analysis")
    parser.add_argument("--data", default="data/cairo_temperatures.csv")
    parser.add_argument("--trend", action="store_true", help="Print the yearly warming trend")
    parser.add_argument("--seasonal", action="store_true", help="Print the monthly seasonal profile")
    parser.add_argument("--heatwaves", action="store_true", help="Print heatwave day counts per year")
    parser.add_argument("--chart", metavar="DIR", help="Save trend + seasonal charts into DIR")
    args = parser.parse_args()

    df = load_data(args.data)

    if args.trend or not (args.seasonal or args.heatwaves or args.chart):
        slope = trend_slope(df)
        print(f"Warming trend: {slope:+.3f}°C/year (avg daily high)")
        for year, value in yearly_trend(df).items():
            print(f"  {year}: {value:.1f}°C avg high")

    if args.seasonal:
        hot_month, hot_temp = hottest_month(df)
        cold_month, cold_temp = coldest_month(df)
        print(f"\nHottest month: {hot_month} ({hot_temp:.1f}°C avg high)")
        print(f"Coldest month: {cold_month} ({cold_temp:.1f}°C avg high)")

    if args.heatwaves:
        print("\nHeatwave days (>40°C) per year:")
        for year, count in heatwave_days_per_year(df).items():
            print(f"  {year}: {count}")

    if args.chart:
        import os

        os.makedirs(args.chart, exist_ok=True)
        plot_yearly_trend(df, os.path.join(args.chart, "yearly_trend.png"))
        plot_seasonal_profile(df, os.path.join(args.chart, "seasonal_profile.png"))
        print(f"\nSaved charts to {args.chart}/")


if __name__ == "__main__":
    main()
