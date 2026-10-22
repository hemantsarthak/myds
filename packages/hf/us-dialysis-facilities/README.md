---
license: cc0-1.0
task_categories:
- tabular-classification
tags:
- open-data
- healthcare
- medicare
- cms
- dialysis
- tabular
pretty_name: US Dialysis Facilities (CMS)
size_categories:
- 1K<n<10K
---

# US Dialysis Facilities (CMS)

Medicare-certified dialysis facilities with the CMS five-star rating, survival, hospitalisation, readmission and transfusion measures, services and station counts.

- **Records:** 7,490 (this repo ships a random sample of a few hundred rows; the full data is
  served by the directory)
- **Live browsable directory:** <https://dialysis.tekify.xyz>
- **Source:** CMS Provider Data Catalog — Dialysis Facility Listing
- **Licence:** cc0-1.0

## Files

- `sample.csv` — random sample with the full column set

## Data access

The full dataset is available as a JSON index at the directory's `/data/` path (no API key, CORS
enabled) and documented at <https://hemantsarthak.github.io/myds/data.html>.

## Citation

Cite the original source (CMS Provider Data Catalog — Dialysis Facility Listing). The derived sample and card are released under the same
licence as the source.
