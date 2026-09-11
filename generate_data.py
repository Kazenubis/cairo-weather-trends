"""
Generates data/cairo_temperatures.csv — a synthetic but climate-realistic
5-year daily temperature record for Cairo, Egypt.

This sandbox has no outbound network access, so this isn't scraped from a
real weather API — it's built from Cairo's actual known seasonal profile
(hot, dry summers with highs regularly above 35C and occasional 40C+
heatwaves in July/August; mild winters with highs around 18-20C and lows
near 9-10C) plus a small embedded warming trend and daily random noise, so
the analysis has genuine seasonal and multi-year structure to find.

Re-run this file to regenerate the CSV (it's seeded, so the output is
reproducible).
"""

import csv
import math
import random
from datetime import date, timedelta

START = date(2021, 1, 1)
END = date(2025, 12, 31)
SEED = 11

# Approximate real Cairo monthly average highs/lows (Celsius) — the
# seasonal shape the synthetic data is built around.
MONTHLY_AVG_HIGH = {
    1: 19, 2: 21, 3: 24, 4: 29, 5: 33, 6: 35,
    7: 36, 8: 35, 9: 33, 10: 29, 11: 24, 12: 20,
}
MONTHLY_AVG_LOW = {
    1: 9, 2: 10, 3: 12, 4: 16, 5: 19, 6: 21,
    7: 22, 8: 22, 9: 21, 10: 18, 11: 14, 12: 10,
}

WARMING_TREND_PER_YEAR = 0.04  # degrees C/year — a small embedded drift
HEATWAVE_CHANCE_SUMMER = 0.04   # chance any given June-Aug day spikes


def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def generate():
    rng = random.Random(SEED)
    rows = []
    for d in daterange(START, END):
        years_since_start = (d - START).days / 365.25
        base_high = MONTHLY_AVG_HIGH[d.month]
        base_low = MONTHLY_AVG_LOW[d.month]
        warming = WARMING_TREND_PER_YEAR * years_since_start

        temp_max = base_high + warming + rng.gauss(0, 1.8)
        temp_min = base_low + warming + rng.gauss(0, 1.4)

        if d.month in (6, 7, 8) and rng.random() < HEATWAVE_CHANCE_SUMMER:
            temp_max += rng.uniform(4, 7)  # a heatwave spike

        humidity = 55 + 15 * math.sin((d.month - 7) / 12 * 2 * math.pi) + rng.gauss(0, 4)
        humidity = max(20, min(90, humidity))

        rows.append({
            "date": d.isoformat(),
            "temp_max_c": round(temp_max, 1),
            "temp_min_c": round(min(temp_min, temp_max - 1), 1),
            "humidity_pct": round(humidity, 1),
        })
    return rows


def main():
    rows = generate()
    with open("data/cairo_temperatures.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "temp_max_c", "temp_min_c", "humidity_pct"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} days to data/cairo_temperatures.csv")


if __name__ == "__main__":
    main()
