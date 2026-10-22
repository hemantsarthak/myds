# STATE — current status

> Last updated: 2026-10-22 ~16:20 IST (DeepSeek agent, repo `myds`). Round 2 of the goal loop.
> Next session: read this, then `docs/BACKLOG.md`; pick the top ready item. Do not re-plan.

## One-line status

**6 properties live (~86.7k pages) with HilltopAds + self-hosted analytics; all sitemaps submitted to
IndexNow; Bing indexes within an hour but ranking is not there yet (new domain). Revenue $0;
traffic is the only missing input and it is a matter of indexing time. Affiliate signups in
progress (teammate `affiliate`).**

## Live properties (ours — Cloudflare Pages, free tier)

| Site | Project | URL | Pages | Ads | Analytics |
|---|---|---|---|---|---|
| Hub | `hub` | https://tekify.xyz | 5 | ✅ | ✅ |
| IFSC Codes India | `ifsc` | https://ifsccodes.tekify.xyz | 19,511 | ✅ | ✅ |
| Airport Codes | `myds-airport` | https://airportcodes.tekify.xyz | 10,181 | ✅ | ✅ |
| US ZIP Codes | `myds-zip` | https://zipcodes.tekify.xyz | 17,759 | ✅ | ✅ |
| US Places & Counties | `myds-places` | https://places.tekify.xyz | 19,203 | ✅ | ✅ |
| Calculators | `myds-calculators` | https://calculators.tekify.xyz | 62 | ✅ | ✅ |

≈ **86,700 pages** ours. Every page: canonical, JSON-LD, breadcrumbs, sitemap, robots, IndexNow
key, network cross-links, ad slots, analytics beacon.

NOT ours (shared Cloudflare account, **never touch**): `pincode.tekify.xyz` (project
`pincode-india`), `ifsc.tekify.xyz` (project `ifsc-india`), `solar` — the Minimax agent deploys
those. `scripts/build_all.py` deploys only our six projects.

## Money infrastructure (autonomous, no KYC)

- **Ads — HilltopAds LIVE.** Account 409868, site `tekify.xyz` (925719, DNS verified). Zones:
  in-page push 7541137, banner 300x250 7541153, popunder 7541169. `engine/ads.py` is the single
  source; every page carries the tags. Payout: min $20, weekly Tue, Net7, crypto OK.
  Headless: `python workers/adsprobe/hilltop_api.py sites`. Docs: `docs/ADS.md`.
  **TODO: paste payout address into the panel once balance > 0.**
- **Analytics — self-hosted** Worker+KV; `python scripts/ops.py stats --site all --days 7`.
  Docs: `docs/ANALYTICS.md`.
- **Email — autonomous inbox** `*@tekify.xyz`; `python scripts/ops.py inbox --latest --to <addr>`.
  Docs: `docs/MAILBOX.md`.
- **Affiliate — Travelpayouts LIVE** (approved 2026-10-22; partner 764877, marker 793747).
  137 travel brands behind one account; 15 tracked links in `engine/affiliates.py`. Disclosed
  cards (`rel="sponsored nofollow noopener"`) are wired into **airport pages** (flight
  compensation, eSIM, flights) and the **hub** (hosting + travel). Hostinger submitted (manual
  review); Cuelinks email-confirmed (needs one browser login). Docs: `docs/AFFILIATE.md`.
- **Payout wallet**: BTC `bc1qn7v2m9gf599ureygujpwewf9qvxay62lel86rd`,
  USDT-TRC20 `TBAvcRpbbWDvrc8emV6KecNN1tsmCacYvb`, ETH `0x20778d136055522f27ecacc0f7F49378E1E9a91A`.
  Keys: `shared/wallets-payout.json` (gitignored).
- **Repo** `hemantsarthak/myds` (public) = durable memory; secrets only in `shared/`.

## Round-2 work (2026-10-22 afternoon)

1. Launched `places.tekify.xyz` — 16,000 US places + 3,144 counties + 51 states, built from
   Census Vintage-2023 population estimates, the 2023 Gazetteer and place→county relationships.
   Answers "what county is X in", population, coordinates, time zone, nearby places.
   Fixed three data/copy bugs (county name duplication, duplicate titles for same-named places).
2. Expanded IFSC from 15,086 → 19,507 pages (14,000 → 18,500 branch pages) to maximise the
   long-tail coverage of India's bank-branch lookups on the domain that already has history.
3. IndexNow: places site fully accepted (19,200 URLs after the per-host verification settled);
   IFSC re-submitted after expansion.
'4. Affiliate: Travelpayouts approved; 15 tracked links wired into airport pages + hub.
5. Guide content: 10 hand-written explainers live under `/guides/` on all five data sites
   (`engine/guides.py`), linked from the nav, to lift site quality and capture informational
   queries. IndexNow re-submitted for all five (86.7k URLs accepted).'

## Verified facts

- All six properties return 200 and carry ad + analytics scripts.
- IndexNow accepted: ifsc 19,507 (re-submitted), airport 10,178, zip 17,756, places 19,200,
  calculators 60, hub 4; pincode 8,626 earlier (host now the other agent's).
- Bing `site:` shows results for every property; no head-query rankings yet.
- Calculator maths: 11/11 closed-form checks pass (`python sites/calculators/check_formulas.py`).
- Analytics beacon verified in production (real pageviews recorded).

## Next actions

1. Wire affiliate blocks (from teammate) into calculator pages + hosting/VPN-adjacent pages;
   rebuild + redeploy; track clicks via the analytics worker (add a `/go` redirect worker if needed).
2. New properties: `areacodes.tekify.xyz` (NANP + world dialing codes), `swiftcodes.tekify.xyz`.
3. If traffic appears (>~50 visits/day): tune ads (consider disabling popunder), add
   affiliate CTAs, and start collecting email subscribers (optional).
4. Weekly: `ops.py stats`, `docs/REVENUE.md`, prune/expand. Monthly: re-run IndexNow after changes.
5. Consider a GitHub Actions daily job: re-submit IndexNow for changed sitemaps + commit a stats
   snapshot (keeps progress going when the laptop is off).

## Known issues

- Pincode project is the other agent's (our sources kept for reference).
- Ad zones show no fill at zero traffic; ad divs render empty (cosmetic).
- IFSC branch page has a harmless redundant sentence; fix opportunistically.
- Cloudflare Pages free = 20,000 files/deployment: ifsc 19,586, zip 17.7k, places 19.2k are at the
  ceiling — further growth needs a second project/subdomain or a dynamic Worker.
