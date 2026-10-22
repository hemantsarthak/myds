#!/usr/bin/env python3
"""Fetch the US ZIP dataset used by sites/zip.

Sources (all public / open):
  * GeoNames US postal codes  https://download.geonames.org/export/zip/US.zip        (CC BY 4.0)
  * GeoNames cities500        https://download.geonames.org/export/dump/cities500.zip (CC BY 4.0)
Output: <repo>/.cache/geonames-us/{US.txt,cities500.txt}   (gitignored)

Run: python sites/zip/fetch_data.py
"""
import pathlib
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
OUT = CACHE / "geonames-us"


def get(name, url):
    zpath = CACHE / name
    if not zpath.exists():
        print("downloading", url)
        urllib.request.urlretrieve(url, zpath)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(OUT)
    print("ok", name, (OUT / name.replace(".zip", ".txt")))


def main():
    CACHE.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    get("US.zip", "https://download.geonames.org/export/zip/US.zip")
    get("cities500.zip", "https://download.geonames.org/export/dump/cities500.zip")


if __name__ == "__main__":
    main()
