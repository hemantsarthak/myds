#!/usr/bin/env python3
"""Fetch the CMS hospital data used by sites/hospitals.

Source: CMS Provider Data Catalog — "Hospital General Information" (public domain).
  https://data.cms.gov/provider-data/dataset/xubh-q36u

Output: <repo>/.cache/hospital_general.csv  (~1.4 MB, 5,400 hospitals)
Run: python sites/hospitals/fetch_data.py
"""
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
META = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/xubh-q36u"
UA = {"User-Agent": "Mozilla/5.0"}


def main() -> None:
    CACHE.mkdir(exist_ok=True)
    out = CACHE / "hospital_general.csv"
    if out.exists() and out.stat().st_size > 100_000:
        print(f"cached: {out} ({out.stat().st_size/1e6:.2f} MB)")
        return
    print("resolving download URL from CMS metastore…")
    with urllib.request.urlopen(urllib.request.Request(META, headers=UA), timeout=60) as r:
        meta = json.loads(r.read().decode())
    url = meta["distribution"][0]["downloadURL"]
    print("downloading", url)
    urllib.request.urlretrieve(url, out)
    print(f"saved {out} ({out.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
