# tekify-data (Python)

Free reference data for the US and India from a keyless JSON API.

- **US ZIP codes** — city, county, state, population, time zone
- **CMS healthcare** — hospital, nursing-home, home-health and dialysis ratings
- **US colleges** — admissions, tuition, net price (IPEDS)
- **US places** — population estimates and county
- **Airports** — IATA/ICAO codes, city, country
- **Area codes** — NANP and world dialing codes
- **Indian IFSC bank codes** — every branch of a bank

No API key. No rate limit. Sources are public domain or openly licensed (US Census Bureau, CMS,
NCES/IPEDS, GeoNames CC BY, OurAirports, Razorpay IFSC MIT) — attribute the original agency.

Full documentation: <https://hemantsarthak.github.io/myds/data.html>

## Install

```bash
pip install tekify-data
```

## Usage

```python
from tekify_data import zip_code, hospitals, ifsc_bank

zip_code("90210")
# {'zip': '90210', 'city': 'Beverly Hills', 'state': 'CA', 'county': 'Los Angeles', ...}

hospitals("Johns Hopkins", limit=3)
# [{'name': ..., 'city': 'Baltimore', 'state': 'MD', 'rating': '3', 'url': '/hospital/...'}]

len(ifsc_bank("HDFC"))   # 11007 branches
```

Each dataset is fetched once and cached in memory for the process.

## Links

- Data documentation: <https://hemantsarthak.github.io/myds/data.html>
- Live directories: <https://tekify.xyz/>
- Dataset samples: <https://github.com/hemantsarthak/myds/tree/main/datasets>
- Source: <https://github.com/hemantsarthak/myds>

## Licence

MIT for this client. The data keeps its original licences (public domain, CC BY 4.0, MIT).
