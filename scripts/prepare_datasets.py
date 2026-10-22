"""Prepare the portfolio's open datasets for publishing: sample CSVs + dataset cards that link to the
live directories. These go in the public repo (github.com/hemantsarthak/myds) and are the payload for
Hugging Face / Zenodo uploads once the inbox quota resets."""
import csv
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache"
OUT = ROOT / "datasets"
random.seed(42)

DATASETS = [
    dict(
        slug="ifsc-codes", src="ifsc.csv",
        title="Indian Bank IFSC Codes",
        site="https://ifsccodes.tekify.xyz",
        source="Razorpay IFSC dataset (MIT licence), mirroring the Reserve Bank of India branch list",
        licence="MIT (source) — attribution required",
        description="Every Indian bank branch with its IFSC code, address, district, state, MICR code and the transfer rails it supports (NEFT/RTGS/IMPS/UPI). 183,208 records.",
        columns="BANK, IFSC, BRANCH, CENTRE, DISTRICT, STATE, ADDRESS, CONTACT, IMPS, RTGS, CITY, ISO3166, NEFT, MICR, UPI, SWIFT",
        sample=200,
    ),
    dict(
        slug="us-zip-codes", src="us-zip-codes.csv",
        title="US ZIP Codes",
        site="https://zipcodes.tekify.xyz",
        source="US Census Bureau / GeoNames (public domain, CC BY 4.0)",
        licence="Public domain / CC BY 4.0",
        description="US ZIP codes with city, state, county, coordinates and population, plus links to the places and area codes that overlap them.",
        columns="zip, city, state, state_name, type, county_fips, county_name, county_fips_all, lat, lng, coord_source, is_zcta, parent_zcta, population",
        sample=300,
    ),
    dict(
        slug="cms-hospital-ratings", src="hospital_general.csv",
        title="US Hospital Ratings (CMS)",
        site="https://hospitals.tekify.xyz",
        source="CMS Provider Data Catalog — Hospital General Information (public domain)",
        licence="Public domain (US Government work)",
        description="Every Medicare-certified US hospital with its CMS overall star rating, ownership, type, emergency-services flag and quality measure counts.",
        columns="Facility ID, Facility Name, Address, City/Town, State, ZIP Code, County/Parish, Telephone Number, Hospital Type, Hospital Ownership, Emergency Services, Hospital overall rating",
        sample=300,
    ),
    dict(
        slug="us-dialysis-facilities", src="dialysis.csv",
        title="US Dialysis Facilities (CMS)",
        site="https://dialysis.tekify.xyz",
        source="CMS Provider Data Catalog — Dialysis Facility Listing (public domain)",
        licence="Public domain (US Government work)",
        description="Medicare-certified dialysis facilities with the CMS five-star rating, survival/hospitalisation/readmission measures, services offered and station counts.",
        columns="CMS Certification Number (CCN), Facility Name, City/Town, State, ZIP Code, Profit or Non-Profit, Chain Organization, # of Dialysis Stations, Offers in-center hemodialysis, Five Star",
        sample=300,
    ),
]


def main():
    OUT.mkdir(exist_ok=True)
    index_rows = []
    for d in DATASETS:
        src = CACHE / d["src"]
        if not src.exists():
            print("missing source:", d["src"])
            continue
        with src.open(encoding="utf-8-sig", errors="replace") as f:
            r = csv.reader(f)
            hdr = next(r)
            rows = list(r)
        folder = OUT / d["slug"]
        folder.mkdir(exist_ok=True)
        sample = random.sample(rows, min(d["sample"], len(rows)))
        with (folder / "sample.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(hdr)
            w.writerows(sample)
        card = f"""# {d['title']}

{d['description']}

- **Live browsable directory:** [{d['site']}]({d['site']})
- **Records:** {len(rows):,}
- **Source:** {d['source']}
- **Licence:** {d['licence']}
- **Sample:** `sample.csv` (first {len(sample)} random rows, same columns as the full file)

## Columns

`{d['columns']}`

## Why this exists

The Tekify network turns public datasets into readable pages, one record per page, with the fields
that matter and links to the surrounding records. This folder publishes a sample of the same data so
you can evaluate it before using the directory, and so the dataset can be mirrored to open-data
platforms (Hugging Face, Zenodo) with the same provenance.

## Citation

If you use the data, cite the original source above. The derived sample and dataset card are released
under the same licence as the source.
"""
        (folder / "README.md").write_text(card, encoding="utf-8")
        index_rows.append((d["title"], d["slug"], len(rows), d["site"]))
        print("prepared", d["slug"], len(rows), "rows ->", len(sample), "sampled")

    index = ["# Open datasets", "",
             "Samples and dataset cards for the public datasets behind the Tekify directories. "
             "Each folder has a README with provenance and a `sample.csv`.", "",
             "| Dataset | Records | Live directory |", "|---|---|---|"]
    for title, slug, n, site in index_rows:
        index.append(f"| [{title}]({slug}/README.md) | {n:,} | [{site}]({site}) |")
    index += ["", "The full data is served by each directory as JSON under `/data/` "
              "(for example <https://zipcodes.tekify.xyz/data/zips.json>).", ""]
    (OUT / "README.md").write_text("\n".join(index), encoding="utf-8")
    print("index written:", len(index_rows), "datasets")


if __name__ == "__main__":
    main()
