---
license: mit
task_categories:
- tabular-classification
tags:
- open-data
- india
- banking
- ifsc
- tabular
pretty_name: Indian Bank IFSC Codes
size_categories:
- 1K<n<10K
---

# Indian Bank IFSC Codes

Every Indian bank branch with its IFSC code, bank, branch, address, district, state, MICR code and supported transfer rails (NEFT, RTGS, IMPS, UPI).

- **Records:** 183,214 (this repo ships a random sample of a few hundred rows; the full data is
  served by the directory)
- **Live browsable directory:** <https://ifsccodes.tekify.xyz>
- **Source:** Razorpay IFSC dataset (MIT licence), mirroring the Reserve Bank of India branch list
- **Licence:** mit

## Files

- `sample.csv` — random sample with the full column set

## Data access

The full dataset is available as a JSON index at the directory's `/data/` path (no API key, CORS
enabled) and documented at <https://hemantsarthak.github.io/myds/data.html>.

## Citation

Cite the original source (Razorpay IFSC dataset (MIT licence), mirroring the Reserve Bank of India branch list). The derived sample and card are released under the same
licence as the source.
