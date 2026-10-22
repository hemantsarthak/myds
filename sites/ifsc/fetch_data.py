#!/usr/bin/env python3
"""Fetch the IFSC dataset used by sites/ifsc.

Source : https://github.com/razorpay/ifsc  (MIT licence; built from NPCI/RBI listings)
Release: v2.0.62 -> IFSC.csv (183k branches, 16 fields)
Output : <repo>/.cache/ifsc.csv   (gitignored, 36 MB)

Run:  python sites/ifsc/fetch_data.py
"""
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
VERSION = "v2.0.62"
URL = f"https://github.com/razorpay/ifsc/releases/download/{VERSION}/IFSC.csv"


def main() -> None:
    CACHE.mkdir(exist_ok=True)
    out = CACHE / "ifsc.csv"
    if out.exists() and out.stat().st_size > 10_000_000:
        print(f"cached: {out} ({out.stat().st_size/1e6:.1f} MB)")
        return
    print("downloading", URL)
    urllib.request.urlretrieve(URL, out)
    print(f"saved {out} ({out.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
