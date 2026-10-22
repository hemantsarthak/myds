#!/usr/bin/env python3
"""Fetch the open data behind sites/areacodes (areacodes.tekify.xyz).

All sources are openly licensed; the build page credits each one.

  us-zip-codes.csv          41,711 US ZIPs -> town, county, coords, population and NANPA
                            area codes. Published by zipcodes.pro under CC BY 4.0
                            (attribution is required and printed in the site footer).
  ca-area-code-cities.csv   Canadian area codes by city (Area-Code-Geolocation-Database).
  ca-area-code-geo.csv      Canadian area code centroids.
  country-codes.csv         UN M49 country list with international dialling codes
                            (datasets/country-codes, public domain / CC).
  geonames-us/cities500.txt GeoNames cities with population and IANA time zone (CC BY 4.0).
                            Shared with the places site; downloaded here if absent.

Output: <repo>/.cache/
Run:    python sites/areacodes/fetch_data.py
"""
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
SOURCES = [
    ("us-zip-codes.csv",
     "https://zipcodes.pro/download/us-zip-codes.csv", "zipcodes.pro, CC BY 4.0"),
    ("ca-area-code-cities.csv",
     "https://raw.githubusercontent.com/ravisorg/Area-Code-Geolocation-Database/master/ca-area-code-cities.csv",
     "Area-Code-Geolocation-Database"),
    ("ca-area-code-geo.csv",
     "https://raw.githubusercontent.com/ravisorg/Area-Code-Geolocation-Database/master/ca-area-code-geo.csv",
     "Area-Code-Geolocation-Database"),
    ("country-codes.csv",
     "https://raw.githubusercontent.com/datasets/country-codes/main/data/country-codes.csv",
     "UN M49 via datasets/country-codes"),
    ("geonames-us/cities500.txt",
     "https://download.geonames.org/export/dump/cities500.zip",
     "GeoNames, CC BY 4.0 (zip: unzip to cities500.txt)"),
]


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, url, licence in SOURCES:
        out = CACHE / name
        if out.exists() and out.stat().st_size > 1024:
            print(f"{name}: present ({out.stat().st_size/1e6:.2f} MB) — {licence}")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {url}")
        urllib.request.urlretrieve(url, out)
        print(f"{name}: {out.stat().st_size/1e6:.2f} MB — {licence}")
    print("\nNote: cities500 arrives as a .zip; unzip it before building if the .txt is missing.")


if __name__ == "__main__":
    main()
