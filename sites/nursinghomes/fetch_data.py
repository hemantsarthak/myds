#!/usr/bin/env python3
"""Fetch the CMS nursing-home data used by sites/nursinghomes.

Source: CMS Provider Data Catalog — "Provider Information" (nursing homes), public domain.
  https://data.cms.gov/provider-data/dataset/4pq5-n9py

Output: <repo>/.cache/nursing_homes.csv  (~9 MB, ~14,700 facilities)
Run: python sites/nursinghomes/fetch_data.py
"""
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
META = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/4pq5-n9py"
UA = {"User-Agent": "Mozilla/5.0"}


def main() -> None:
    CACHE.mkdir(exist_ok=True)
    out = CACHE / "nursing_homes.csv"
    if out.exists() and out.stat().st_size > 1_000_000:
        print(f"cached: {out} ({out.stat().st_size/1e6:.1f} MB)")
        return
    print("resolving download URL from CMS metastore…")
    with urllib.request.urlopen(urllib.request.Request(META, headers=UA), timeout=60) as r:
        meta = json.loads(r.read().decode())
    url = meta["distribution"][0]["downloadURL"]
    print("downloading", url)
    urllib.request.urlretrieve(url, out)
    print(f"saved {out} ({out.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
