---
license: cc-by-4.0
task_categories:
- tabular-classification
tags:
- open-data
- united-states
- geography
- zip-codes
- tabular
pretty_name: US ZIP Codes
size_categories:
- 1K<n<10K
---

# US ZIP Codes

US ZIP codes with city, state, county, coordinates and population.

- **Records:** 41,711 (this repo ships a random sample of a few hundred rows; the full data is
  served by the directory)
- **Live browsable directory:** <https://zipcodes.tekify.xyz>
- **Source:** US Census Bureau / GeoNames
- **Licence:** cc-by-4.0

## Files

- `sample.csv` — random sample with the full column set

## Data access

The full dataset is available as a JSON index at the directory's `/data/` path (no API key, CORS
enabled) and documented at <https://hemantsarthak.github.io/myds/data.html>.

## Citation

Cite the original source (US Census Bureau / GeoNames). The derived sample and card are released under the same
licence as the source.
