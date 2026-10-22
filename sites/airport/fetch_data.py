#!/usr/bin/env python3
"""Fetch the OurAirports dataset used by sites/airport.

Source : https://ourairports.com/data/  (public domain, updated regularly)
Files  : airports.csv (86k), runways.csv (269k), countries.csv, regions.csv
Output : <repo>/.cache/*.csv (gitignored)

Run: python sites/airport/fetch_data.py
"""
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
BASE = "https://davidmegginson.github.io/ourairports-data/"


def main() -> None:
    CACHE.mkdir(exist_ok=True)
    for name in ("airports.csv", "runways.csv", "countries.csv", "regions.csv"):
        out = CACHE / name
        if out.exists() and out.stat().st_size > 1000:
            print(f"cached: {name} ({out.stat().st_size/1e6:.2f} MB)")
            continue
        print("downloading", BASE + name)
        urllib.request.urlretrieve(BASE + name, out)
        print(f"saved {name} ({out.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
