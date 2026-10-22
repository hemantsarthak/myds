# SITES — registry of deployed properties

Updated 2026-10-22. Cloudflare account `c01fe438c7960466670d312e55164037`, domain `tekify.xyz`.

| Site | Pages project | pages.dev subdomain | Public URL | Pages | Ads | Analytics | Status |
|---|---|---|---|---|---|---|---|
| Hub | `hub` | hub-1xy.pages.dev | https://tekify.xyz | 4 | — | — | LIVE |
| Pincode India | `pincode-india` | pincode-india.pages.dev | https://pincode.tekify.xyz | 8,636 | — | — | LIVE |
| IFSC Codes India | `ifsc` | ifsc-b55.pages.dev | https://ifsccodes.tekify.xyz | 15,086 | — | — | LIVE |
| Airport Codes | `myds-airport` | myds-airport.pages.dev | https://airportcodes.tekify.xyz | 10,180 | — | — | LIVE |
| US ZIP Codes | `myds-zip` | myds-zip.pages.dev | https://zipcodes.tekify.xyz | 17,758 | — | — | deploying |

Total published pages ≈ **51,600**.

## Build / deploy commands

```
python sites/<slug>/build.py                     # engine sites (hub, ifsc, airport, zip)
python sites/pincode-india/build_site.py         # legacy template
python scripts/ops.py deploy --project <project> --dir sites/<slug>/site
python scripts/ops.py attach --project <project> --domain <sub>.tekify.xyz
python scripts/ops.py indexnow --dir sites/<slug>/site --host <sub>.tekify.xyz
python scripts/build_all.py --deploy             # everything at once
```

## IMPORTANT — shared Cloudflare account

A **second (Minimax) agent shares this Cloudflare account and domain**. It has taken
`ifsc.tekify.xyz` (project `ifsc-india`) and creates projects like `solar`. Rules:
- Before naming a new site, run `python scripts/ops.py pages` and check for collisions.
- Use the `myds-` prefix for Pages project names and distinct public subdomains
  (`ifsccodes.`, `airportcodes.`, `zipcodes.`, `areacodes.`, `calculators.`).
- Never modify or delete the other agent's projects/DNS records.
- Apex `tekify.xyz` is ours (hub) as of 2026-10-22.

## Planned next sites

areacodes.tekify.xyz (dialing codes) · calculators.tekify.xyz (money/health/date tools) ·
textools.tekify.xyz · swift.tekify.xyz · api.tekify.xyz (paid dataset API)
