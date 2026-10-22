# Indian Bank IFSC Codes

Every Indian bank branch with its IFSC code, address, district, state, MICR code and the transfer rails it supports (NEFT/RTGS/IMPS/UPI). 183,208 records.

- **Live browsable directory:** [https://ifsccodes.tekify.xyz](https://ifsccodes.tekify.xyz)
- **Records:** 183,214
- **Source:** Razorpay IFSC dataset (MIT licence), mirroring the Reserve Bank of India branch list
- **Licence:** MIT (source) — attribution required
- **Sample:** `sample.csv` (first 200 random rows, same columns as the full file)

## Columns

`BANK, IFSC, BRANCH, CENTRE, DISTRICT, STATE, ADDRESS, CONTACT, IMPS, RTGS, CITY, ISO3166, NEFT, MICR, UPI, SWIFT`

## Why this exists

The Tekify network turns public datasets into readable pages, one record per page, with the fields
that matter and links to the surrounding records. This folder publishes a sample of the same data so
you can evaluate it before using the directory, and so the dataset can be mirrored to open-data
platforms (Hugging Face, Zenodo) with the same provenance.

## Citation

If you use the data, cite the original source above. The derived sample and dataset card are released
under the same licence as the source.
