#!/usr/bin/env python3
"""Fetch the IPEDS college data used by sites/colleges.

Source: US Department of Education, National Center for Education Statistics (NCES), IPEDS
        Data Center — public domain. Files are the provisional 2023 releases.

  HD2023      institutional directory (name, address, sector, coordinates, website)
  ADM2023     admissions: applicants, admitted, enrolled, test scores
  IC2023_AY   charges: tuition & fees, in-state / out-of-state
  EF2023A     fall enrollment (EFALEVEL=1 is the all-students total)
  GR2023      150% graduation rates (GRTYPE 2 = adjusted cohort, 3 = completers)

Output: <repo>/.cache/ipeds/<file>/<file>.csv
Run: python sites/colleges/fetch_data.py
"""
import pathlib
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache" / "ipeds"
BASE = "https://nces.ed.gov/ipeds/datacenter/data/"
FILES = ("HD2023", "ADM2023", "IC2023_AY", "EF2023A", "GR2023")


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        zpath = CACHE / f"{name}.zip"
        out = CACHE / name
        if not (out.exists() and any(out.glob("*.csv"))):
            if not zpath.exists():
                print("downloading", BASE + name + ".zip")
                urllib.request.urlretrieve(BASE + name + ".zip", zpath)
            out.mkdir(exist_ok=True)
            with zipfile.ZipFile(zpath) as zf:
                zf.extractall(out)
        csvs = list(out.glob("*.csv"))
        print(f"{name}: {csvs[0].name} ({csvs[0].stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
