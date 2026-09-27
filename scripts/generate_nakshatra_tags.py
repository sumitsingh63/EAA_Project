"""
Generate daily Nakshatra (and solar longitude) tags using the Swiss Ephemeris.

Computes, for every day in a date range:
    - Sun's sidereal longitude (Lahiri ayanamsa)  -> solar Nakshatra + pada
    - Moon's sidereal longitude (Lahiri ayanamsa)  -> lunar Nakshatra + pada

Traditional agricultural markers (e.g. "Sun enters Ardra Nakshatra" as a
monsoon-onset indicator) use the SOLAR Nakshatra. The daily Panchang
Nakshatra (used for muhurta/daily almanac purposes) is the LUNAR one.
Both are included so you can choose per-analysis; the synopsis's framing
points to the solar column as primary.

Install dependencies first:
    pip install pyswisseph pandas

Usage:
    python generate_nakshatra_tags.py
    python generate_nakshatra_tags.py --start 1901-01-01 --end 2025-12-31 --out nakshatra_tags.csv
"""

import argparse
import sys
from datetime import date, timedelta

import pandas as pd

try:
    import swisseph as swe
except ImportError:
    sys.exit("pyswisseph is not installed. Run: pip install pyswisseph")


NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_SPAN = 360.0 / 27.0   # 13.3333... degrees
PADA_SPAN = NAKSHATRA_SPAN / 4  # 3.3333... degrees


def sidereal_longitude(jd_ut, planet):
    """Return sidereal longitude (0-360) of a planet using Lahiri ayanamsa."""
    xx, _ = swe.calc_ut(jd_ut, planet, swe.FLG_SIDEREAL)
    return xx[0] % 360.0


def nakshatra_and_pada(longitude):
    """Map a sidereal longitude to (nakshatra_name, pada 1-4)."""
    nak_index = int(longitude // NAKSHATRA_SPAN) % 27
    pada = int((longitude % NAKSHATRA_SPAN) // PADA_SPAN) + 1
    return NAKSHATRAS[nak_index], pada


def daterange(start_date, end_date):
    days = (end_date - start_date).days
    for n in range(days + 1):
        yield start_date + timedelta(days=n)


def main():
    parser = argparse.ArgumentParser(description="Generate daily solar/lunar Nakshatra tags.")
    parser.add_argument("--start", default="1901-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default="2025-12-31", help="End date YYYY-MM-DD")
    parser.add_argument("--out", default="nakshatra_tags.csv", help="Output CSV path")
    args = parser.parse_args()

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)

    rows = []
    for d in daterange(start_date, end_date):
        # Julian day at 00:00 UT (~5:30 IST); adjust here if you need exact IST midnight
        jd = swe.julday(d.year, d.month, d.day, 0.0)

        sun_lon = sidereal_longitude(jd, swe.SUN)
        moon_lon = sidereal_longitude(jd, swe.MOON)

        sun_nak, sun_pada = nakshatra_and_pada(sun_lon)
        moon_nak, moon_pada = nakshatra_and_pada(moon_lon)

        rows.append({
            "date": d.isoformat(),
            "sun_sidereal_longitude": round(sun_lon, 4),
            "solar_nakshatra": sun_nak,
            "solar_nakshatra_pada": sun_pada,
            "moon_sidereal_longitude": round(moon_lon, 4),
            "lunar_nakshatra": moon_nak,
            "lunar_nakshatra_pada": moon_pada,
        })

        if d.day == 1:
            print(f"Processed through {d.isoformat()}...")

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)

    print(f"\nDone. {len(df):,} rows written to {args.out}")
    print("Columns: date, sun_sidereal_longitude, solar_nakshatra, solar_nakshatra_pada, "
          "moon_sidereal_longitude, lunar_nakshatra, lunar_nakshatra_pada")


if __name__ == "__main__":
    main()