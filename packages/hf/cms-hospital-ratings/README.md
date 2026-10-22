---
license: cc0-1.0
task_categories:
- tabular-classification
tags:
- open-data
- healthcare
- medicare
- cms
- hospitals
- tabular
pretty_name: US Hospital Ratings (CMS)
size_categories:
- 1K<n<10K
---

# US Hospital Ratings (CMS)

Every Medicare-certified US hospital with its CMS overall star rating, ownership, type, emergency-services flag and quality-measure counts.

- **Records:** 5,419 (this repo ships a random sample of a few hundred rows; the full data is
  served by the directory)
- **Live browsable directory:** <https://hospitals.tekify.xyz>
- **Source:** CMS Provider Data Catalog — Hospital General Information
- **Licence:** cc0-1.0

## Files

- `sample.csv` — random sample with the full column set

## Data access

The full dataset is available as a JSON index at the directory's `/data/` path (no API key, CORS
enabled) and documented at <https://hemantsarthak.github.io/myds/data.html>.

## Citation

Cite the original source (CMS Provider Data Catalog — Hospital General Information). The derived sample and card are released under the same
licence as the source.
