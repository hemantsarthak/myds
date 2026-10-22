# tekify-data

Free reference data for the US and India, from a keyless JSON API — with a tiny client for Node 18+.

- **US ZIP codes** — city, county, state, population, time zone
- **CMS healthcare** — hospital, nursing-home, home-health and dialysis ratings
- **US colleges** — admissions, tuition, net price (IPEDS)
- **US places** — population estimates and county
- **Airports** — IATA/ICAO codes, city, country
- **Area codes** — NANP and world dialing codes
- **Indian IFSC bank codes** — every branch of a bank

No API key. No rate limit. CORS enabled. Sources are public domain or openly licensed (US Census Bureau,
CMS, NCES/IPEDS, GeoNames CC BY, OurAirports, Razorpay IFSC MIT) — attribute the original agency.

Full documentation: <https://hemantsarthak.github.io/myds/data.html>

## Install

```bash
npm install tekify-data
```

## Usage

```js
const tekify = require("tekify-data");

// US ZIP lookup
const zip = await tekify.zipCode("90210");
// { zip: "90210", city: "Beverly Hills", state: "CA", county: "Los Angeles", population: ..., timezone: "America/Los_Angeles" }

// CMS hospital ratings
const hospitals = await tekify.hospitals("Johns Hopkins");
// [{ name, city, state, rating, url }]

// Indian bank branches
const branches = await tekify.ifscBank("HDFC");
// [{ ifsc, branch, district, state }]
```

All functions return plain objects; the client caches each dataset in memory after the first fetch.

## Links

- Data documentation: <https://hemantsarthak.github.io/myds/data.html>
- Live directories: <https://tekify.xyz/>
- Dataset samples and cards: <https://github.com/hemantsarthak/myds/tree/main/datasets>
- Source: <https://github.com/hemantsarthak/myds>

## Licence

MIT for this client. The data keeps its original licences (public domain, CC BY 4.0, MIT).
