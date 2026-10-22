#!/usr/bin/env python3
"""Generate Hugging Face dataset cards (packages/hf/<slug>/) from the repo datasets.

HF dataset repos need a README with YAML frontmatter (license, tags, task categories) plus the data
files. The plain-GitHub cards stay in datasets/; these are the upload payload.
"""
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "datasets"
OUT = ROOT / "packages" / "hf"

CARDS = {
    "ifsc-codes": dict(
        title="Indian Bank IFSC Codes",
        site="https://ifsccodes.tekify.xyz",
        license="mit",
        tags=["open-data", "india", "banking", "ifsc", "tabular"],
        source="Razorpay IFSC dataset (MIT licence), mirroring the Reserve Bank of India branch list",
        rows="183,214",
        desc="Every Indian bank branch with its IFSC code, bank, branch, address, district, state, MICR "
             "code and supported transfer rails (NEFT, RTGS, IMPS, UPI).",
    ),
    "us-zip-codes": dict(
        title="US ZIP Codes",
        site="https://zipcodes.tekify.xyz",
        license="cc-by-4.0",
        tags=["open-data", "united-states", "geography", "zip-codes", "tabular"],
        source="US Census Bureau / GeoNames",
        rows="41,711",
        desc="US ZIP codes with city, state, county, coordinates and population.",
    ),
    "cms-hospital-ratings": dict(
        title="US Hospital Ratings (CMS)",
        site="https://hospitals.tekify.xyz",
        license="cc0-1.0",
        tags=["open-data", "healthcare", "medicare", "cms", "hospitals", "tabular"],
        source="CMS Provider Data Catalog — Hospital General Information",
        rows="5,419",
        desc="Every Medicare-certified US hospital with its CMS overall star rating, ownership, type, "
             "emergency-services flag and quality-measure counts.",
    ),
    "us-dialysis-facilities": dict(
        title="US Dialysis Facilities (CMS)",
        site="https://dialysis.tekify.xyz",
        license="cc0-1.0",
        tags=["open-data", "healthcare", "medicare", "cms", "dialysis", "tabular"],
        source="CMS Provider Data Catalog — Dialysis Facility Listing",
        rows="7,490",
        desc="Medicare-certified dialysis facilities with the CMS five-star rating, survival, "
             "hospitalisation, readmission and transfusion measures, services and station counts.",
    ),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, c in CARDS.items():
        folder = OUT / slug
        folder.mkdir(parents=True, exist_ok=True)
        sample = SRC / slug / "sample.csv"
        if sample.exists():
            shutil.copy(sample, folder / "sample.csv")
        card = f"""---
license: {c['license']}
task_categories:
- tabular-classification
tags:
{chr(10).join('- ' + t for t in c['tags'])}
pretty_name: {c['title']}
size_categories:
- 1K<n<10K
---

# {c['title']}

{c['desc']}

- **Records:** {c['rows']} (this repo ships a random sample of a few hundred rows; the full data is
  served by the directory)
- **Live browsable directory:** <{c['site']}>
- **Source:** {c['source']}
- **Licence:** {c['license']}

## Files

- `sample.csv` — random sample with the full column set

## Data access

The full dataset is available as a JSON index at the directory's `/data/` path (no API key, CORS
enabled) and documented at <https://hemantsarthak.github.io/myds/data.html>.

## Citation

Cite the original source ({c['source']}). The derived sample and card are released under the same
licence as the source.
"""
        (folder / "README.md").write_text(card, encoding="utf-8")
        print("card:", slug)


if __name__ == "__main__":
    main()
