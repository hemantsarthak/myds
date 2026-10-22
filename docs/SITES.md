# SITES — registry of deployed properties

Updated 2026-10-22 (round 5). Cloudflare account `c01fe438c7960466670d312e55164037`, domain `tekify.xyz`.

## Ours (we build + deploy these)

| Site | Pages project | pages.dev subdomain | Public URL | Pages | Ads | Analytics | Status |
|---|---|---|---|---|---|---|---|
| Hub | `hub` | hub-1xy.pages.dev | https://tekify.xyz | 4 | ✅ pop+push | ✅ | LIVE |
| IFSC Codes India | `ifsc` | ifsc-b55.pages.dev | https://ifsccodes.tekify.xyz | 19,511 | ✅ pop+push | ✅ | LIVE |
| Airport Codes | `myds-airport` | myds-airport.pages.dev | https://airportcodes.tekify.xyz | 10,181 | ✅ pop+push | ✅ | LIVE |
| US ZIP Codes | `myds-zip` | myds-zip.pages.dev | https://zipcodes.tekify.xyz | 17,759 | ✅ pop+push | ✅ | LIVE |
| US Places & Counties | `myds-places` | myds-places.pages.dev | https://places.tekify.xyz | 19,203 | ✅ pop+push | ✅ | LIVE |
| US Colleges | `myds-colleges` | myds-colleges.pages.dev | https://colleges.tekify.xyz | 6,056 | ✅ pop+push | ✅ | LIVE |
| Calculators | `myds-calculators` | myds-calculators.pages.dev | https://calculators.tekify.xyz | 62 | ✅ pop+push | ✅ | LIVE |
| **Area Codes** | `myds-areacodes` | myds-areacodes.pages.dev | https://areacodes.tekify.xyz | 6,954 | ✅ pop+push | ✅ | LIVE (2026-10-22) |

Total ours ≈ **113,451 pages**. IndexNow accepted for every property (all 79.7k URLs, 2026-10-22).

### Area Codes — what it is (built round 5)

- 398 NANP area codes (US 50 states + DC + territories + Canada) with towns covered, counties,
  population, ZIP codes, time zone, overlapping codes, nearby codes and dialling instructions.
- 6,224 city pages (`/city/<st>-<slug>/`) with the area codes and ZIP codes for each town.
- 248 world country calling codes (`/country/<iso2>/`) with how to call each country.
- Browse indexes (`/area-code/`, `/state/`, `/city/`, `/country-codes/`), a JS search over
  ~7k entries (`/data/search.json`) and 8 hand-written guides (4,150 words).
- Sources: ZIP↔area-code open data (zipcodes.pro, CC BY 4.0), Canadian codes
  (Area-Code-Geolocation-Database), UN M49 country codes, GeoNames time zones. Attribution is in
  the site footer and `/about/`. Re-fetch with `python sites/areacodes/fetch_data.py`.
- Build: `python sites/areacodes/build.py` → `sites/areacodes/site/`.
- Generated output is gitignored (`site/`), sources are committed.

## NOT ours (shared Cloudflare account — do not touch)

The **Minimax agent** shares this account and domain. It actively deploys to:
- `pincode-india` → pincode.tekify.xyz (it re-deployed over our version on 2026-10-22 14:10;
  we handed it over and stopped deploying there)
- `ifsc-india` → ifsc.tekify.xyz (their IFSC lookup; ours is ifsccodes.tekify.xyz)
- `solar` (solar-6f3.pages.dev)

Rules: never modify/delete those projects or DNS; always use `myds-` prefixed project names
+ distinct subdomains; run `python scripts/ops.py pages` before naming anything; expect the
same niche to be attempted by them too (duplication is acceptable, racing is not).

## Build / deploy commands

```
python sites/<slug>/build.py                     # engine sites (hub, ifsc, airport, zip, ...)
python sites/areacodes/build.py                  # area codes (needs .cache/us-zip-codes.csv)
python scripts/ops.py deploy --project <project> --dir sites/<slug>/site
python scripts/ops.py attach --project <project> --domain <sub>.tekify.xyz
python scripts/ops.py indexnow --dir sites/<slug>/site --host <sub>.tekify.xyz
python scripts/ops.py stats --site all --days 7
python scripts/build_all.py --deploy             # everything at once
```

## Planned next sites (myds- prefix, unique subdomains)

`swiftcodes.tekify.xyz` · `api.tekify.xyz` (paid dataset API, x402)
