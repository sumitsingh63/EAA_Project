"""
Download IMD gridded daily rainfall data (2000-2026) and merge into one CSV.

Uses the `imdlib` package to pull IMD's 0.25x0.25 degree gridded daily
rainfall data year by year, then concatenates everything into a single
long-format CSV with columns: date, lat, lon, rain (mm).

Install dependencies first:
    pip install imdlib pandas xarray

Usage:
    python download_imd_rainfall.py
    python download_imd_rainfall.py --start 2000 --end 2026 --outdir imd_data --out imd_rainfall_2000_2026.csv
"""

import argparse
import os
import sys
import pandas as pd

try:
    import imdlib as imd
except ImportError:
    sys.exit("imdlib is not installed. Run: pip install imdlib")


def download_year(year, variable, outdir):
    """Download a single year of IMD data. Returns the imdlib data object or None on failure."""
    try:
        data = imd.get_data(variable, year, year, fn_format='yearwise', file_dir=outdir)
        return data
    except Exception as e:
        print(f"  [WARN] Could not download {year}: {e}")
        return None


def to_long_dataframe(data, year):
    """Convert an imdlib data object for one year into a long-format pandas DataFrame."""
    try:
        ds = data.get_xarray()
    except Exception as e:
        print(f"  [WARN] Could not convert {year} to xarray: {e}")
        return None

    # ds has dims (time, lat, lon) and a data variable (usually 'rain')
    var_name = list(ds.data_vars)[0]
    df = ds[var_name].to_dataframe().reset_index()
    df = df.rename(columns={var_name: "rain_mm", "time": "date"})

    # IMD uses 99.9 as a missing-value flag in the raw grids
    df.loc[df["rain_mm"] >= 99.0, "rain_mm"] = pd.NA

    return df[["date", "lat", "lon", "rain_mm"]]


def main():
    parser = argparse.ArgumentParser(description="Download and merge IMD gridded rainfall data.")
    parser.add_argument("--start", type=int, default=2000, help="Start year (inclusive)")
    parser.add_argument("--end", type=int, default=2026, help="End year (inclusive)")
    parser.add_argument("--variable", default="rain", help="IMD variable name (default: rain)")
    parser.add_argument("--outdir", default="imd_raw_data", help="Directory to cache raw downloaded grid files")
    parser.add_argument("--out", default="imd_rainfall_merged.csv", help="Path for the final merged CSV")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    all_frames = []
    successful_years = []
    failed_years = []

    for year in range(args.start, args.end + 1):
        print(f"Downloading {args.variable} data for {year}...")
        data = download_year(year, args.variable, args.outdir)
        if data is None:
            failed_years.append(year)
            continue

        df = to_long_dataframe(data, year)
        if df is None or df.empty:
            failed_years.append(year)
            continue

        all_frames.append(df)
        successful_years.append(year)

    if not all_frames:
        sys.exit("No data was successfully downloaded for any requested year.")

    print("\nMerging all years into a single dataframe...")
    merged = pd.concat(all_frames, ignore_index=True)
    merged = merged.sort_values(["date", "lat", "lon"]).reset_index(drop=True)

    merged.to_csv(args.out, index=False)

    print(f"\nDone. Merged CSV written to: {args.out}")
    print(f"Rows: {len(merged):,}")
    print(f"Years successfully included: {successful_years}")
    if failed_years:
        print(f"Years that failed or had no data (e.g. not yet released, like the current year): {failed_years}")


if __name__ == "__main__":
    main()