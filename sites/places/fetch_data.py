#!/usr/bin/env python3
"""Fetch US places / county / population data for sites/places.

Sources (all US Census Bureau, public domain):
  * sub-est2023.csv  population estimates for states, counties and places (2023)
  * 2023_Gaz_place_national.txt  place centroids, land area, USPS state code
  * 2023_Gaz_counties_national.txt  county centroids
  * GeoNames cities500.txt (already downloaded by sites/zip) for time zones

Output: <repo>/.cache/{sub-est2023.csv,gaz/2023_Gaz_place_national.txt,gaz/*counties*.txt}
Run: python sites/places/fetch_data.py
"""
import pathlib
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
BASE = "https://www2.census.gov/"


def get(name, url):
    out = CACHE / name
    if out.exists() and out.stat().st_size > 1000:
        print("cached", name)
        return
    print("downloading", url)
    urllib.request.urlretrieve(url, out)
    print("saved", name, f"{out.stat().st_size/1e6:.2f} MB")


def main():
    CACHE.mkdir(exist_ok=True)
    get("sub-est2023.csv",
        BASE + "programs-surveys/popest/datasets/2020-2023/cities/totals/sub-est2023.csv")
    get("gaz_place.zip",
        BASE + "geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_place_national.zip")
    get("gaz_county.zip",
        BASE + "geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_counties_national.zip")
    out = CACHE / "gaz"
    out.mkdir(exist_ok=True)
    for z in ("gaz_place.zip", "gaz_county.zip"):
        with zipfile.ZipFile(CACHE / z) as zf:
            zf.extractall(out)
    print("gazetteers extracted to", out)


if __name__ == "__main__":
    main()
