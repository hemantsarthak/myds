# SITES — registry of deployed properties

Updated 2026-10-22. Cloudflare account `c01fe438c7960466670d312e55164037`, domain `tekify.xyz`.

## Ours (we build + deploy these)

| Site | Pages project | pages.dev subdomain | Public URL | Pages | Ads | Analytics | Status |
|---|---|---|---|---|---|---|---|
| Hub | `hub` | hub-1xy.pages.dev | https://tekify.xyz | 5 | ✅ pop+push | ✅ | LIVE |
| IFSC Codes India | `ifsc` | ifsc-b55.pages.dev | https://ifsccodes.tekify.xyz | 15,086 | ✅ pop+push | ✅ | LIVE |
| Airport Codes | `myds-airport` | myds-airport.pages.dev | https://airportcodes.tekify.xyz | 10,179 | ✅ pop+push | ✅ | LIVE |
| US ZIP Codes | `myds-zip` | myds-zip.pages.dev | https://zipcodes.tekify.xyz | 17,757 | ✅ pop+push | ✅ | LIVE |
| Calculators | `myds-calculators` | myds-calculators.pages.dev | https://calculators.tekify.xyz | 60 | ✅ pop+push | ✅ | LIVE |
| US Places & Counties | `myds-places` | myds-places.pages.dev | https://places.tekify.xyz | 19,200 | ✅ pop+push | ✅ | LIVE |

Total ours ≈ **62,287 pages**. All submitted to IndexNow (2026-10-22, 51.6k URLs incl. pincode).

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
python sites/<slug>/build.py                     # engine sites (hub, ifsc, airport, zip)
python sites/pincode-india/build_site.py         # legacy template (no longer deployed by us)
python scripts/ops.py deploy --project <project> --dir sites/<slug>/site
python scripts/ops.py attach --project <project> --domain <sub>.tekify.xyz
python scripts/ops.py indexnow --dir sites/<slug>/site --host <sub>.tekify.xyz
python scripts/ops.py stats --site all --days 7
python scripts/build_all.py --deploy             # everything at once
```

## Planned next sites (myds- prefix, unique subdomains)

`swiftcodes.tekify.xyz` ·
`areacodes.tekify.xyz` · `api.tekify.xyz` (paid dataset API, x402)
