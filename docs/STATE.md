# STATE — current status

> Last updated: 2026-10-22 ~16:55 IST (DeepSeek agent, repo `myds`). Round 4 of the goal loop.
> Next session: read this, then `docs/BACKLOG.md`; pick the top ready item. Do not re-plan.

## One-line status

**7 properties live (~72,800 pages) with HilltopAds display ads, Travelpayouts affiliate cards,
self-hosted analytics and an autonomous inbox. IndexNow: every URL accepted; crawlers are
rendering pages (99 bot hits on airport, 72 on zip, 59 on ifsc in 3 days). Revenue still $0 —
the domain is 2 days old and ranking is the bottleneck, not infrastructure.**

## Live properties (ours — Cloudflare Pages, free tier)

| Site | Project | URL | Pages | Ads | Analytics |
|---|---|---|---|---|---|
| Hub | `hub` | https://tekify.xyz | 4 | ✅ | ✅ |
| IFSC Codes India | `ifsc` | https://ifsccodes.tekify.xyz | 19,511 | ✅ | ✅ |
| Airport Codes | `myds-airport` | https://airportcodes.tekify.xyz | 10,181 | ✅ | ✅ |
| US ZIP Codes | `myds-zip` | https://zipcodes.tekify.xyz | 17,759 | ✅ | ✅ |
| US Places & Counties | `myds-places` | https://places.tekify.xyz | 19,203 | ✅ | ✅ |
| **US Colleges** | `myds-colleges` | https://colleges.tekify.xyz | 6,056 | ✅ | ✅ |
| Calculators | `myds-calculators` | https://calculators.tekify.xyz | 62 | ✅ | ✅ |

≈ **72,800 pages** ours. Every property: canonical URLs, JSON-LD, breadcrumbs, sitemaps, robots,
IndexNow key, network cross-links (footer), ad slots, analytics beacon; five have a `/guides/`
section of hand-written explainers.

NOT ours (shared Cloudflare account, **never touch**): `pincode.tekify.xyz` (project
`pincode-india`), `ifsc.tekify.xyz` (project `ifsc-india`), `solar` — deployed by the Minimax agent.

## Money infrastructure (autonomous, no KYC)

- **Ads — HilltopAds LIVE.** Account 409868, site `tekify.xyz` (925719, DNS-verified). Zones:
  in-page push 7541137, banner 300x250 7541153, popunder 7541169. Single source: `engine/ads.py`.
  Payout min $20, weekly Tue, Net7, crypto OK. **TODO: paste payout address once balance > 0.**
- **Affiliate — Travelpayouts LIVE** (partner 764877, marker 793747): 15 tracked travel links;
  disclosed cards on all airport pages (compensation/eSIM/flights) and the hub. Hostinger submitted;
  Cuelinks email-confirmed. Docs: `docs/AFFILIATE.md`.
- **Analytics — self-hosted** Worker+KV: `python scripts/ops.py stats --site all --days 7`.
- **Email — autonomous inbox** `*@tekify.xyz`: `python scripts/ops.py inbox --latest --to <addr>`.
- **Payout wallet**: BTC `bc1qn7v2m9gf599ureygujpwewf9qvxay62lel86rd`, USDT-TRC20
  `TBAvcRpbbWDvrc8emV6KecNN1tsmCacYvb`, ETH `0x20778d136055522f27ecacc0f7F49378E1E9a91A`
  (keys in `shared/wallets-payout.json`, gitignored).
- **Repo** `hemantsarthak/myds` (public) = durable memory; secrets only in `shared/`.

## Round-4 work (2026-10-22 evening)

1. **Enriched all 19,203 places pages** with ZIP codes and NANP telephone area codes (joined from
   GeoNames postal data + Area-Code-Geolocation-Database), plus a sister-site link to the ZIP
   directory. Unique facts on a domain Bing is already crawling (141 bot renders on airport, 121
   on zip, 72 on ifsc). Verified live: Austin shows ZIPs 73301…78712 and area codes 512, 737.
2. **Bing Webmaster Tools: fully scripted, blocked on ONE 30-second human check.** Microsoft
   signup with `bingwmt@tekify.xyz` works autonomously end-to-end (email code read from our inbox,
   birthdate, name) up to Microsoft's "press and hold" human check — CAPTCHA-class, not defeated
   (policy). `scripts/bing_submit.py` is ready and resolves all 72,776 URLs (500/batch, per-site
   10k/day quota ledger). After the human press-and-hold: add 7 properties -> DNS TXT verify via
   `scripts/ops.py dns` -> API key to `shared/.env` as `BING_WMT_API_KEY` -> `python
   scripts/bing_submit.py --all`. Docs: `docs/BING.md`. **Biggest indexing lever left.**
3. Confirmed via Bing: **no head or long-tail rankings yet** on any of seven queries probed
   (domain is 2 days old) — indexing has happened (site: shows results) but ranking has not.

## Round-3 work (2026-10-22 afternoon/evening)

1. **New property `colleges.tekify.xyz`** — 5,995 active US institutions from federal IPEDS
   (HD2023 directory, ADM2023 admissions, IC2023_AY charges, EF2023A enrollment, GR2023 150%
   graduation rates). Each page: acceptance rate, applicants/admitted/enrolled, in-state and
   out-of-state tuition, enrollment, graduation + transfer-out rate, SAT/ACT middle 50%, location,
   nearest institutions, website/phone. Plus 52 state pages, 3 guides, local search.
   Verified against known values (Harvard: 3% admit, 30,386 enrolled, $59,076 tuition, 97% grad).
2. Added college guides to `engine/guides.py`; colleges added to hub, footer network and build_all.
3. Cert attach + IndexNow for the new property (6,056 URLs accepted; first attempt 403 until the
   per-host verification settled).

## Verified facts

- 7 properties return 200; ads + analytics present; hub links to every property.
- IndexNow accepted all submissions (ifsc 19,511 · airport 10,181 · zip 17,759 · places 19,203 ·
  colleges 6,056 · calculators 62 · hub 4).
- Bing `site:` returns results for every property; no head-query rankings yet (domain age).
- Calculator maths: 11/11 checks pass (`python sites/calculators/check_formulas.py`).
- Harvard page numbers cross-checked against public IPEDS figures.

## Next actions

1. `areacodes.tekify.xyz` (NANP + world dialing codes) and `swiftcodes.tekify.xyz` — the last two
   planned niches. Redirect/track affiliate clicks with a `/go/` Pages Function on the hub.
2. Watch `ops.py stats` + HilltopAds statistics daily; when traffic > ~50/day, tune ad layout
   (consider disabling the popunder if bounce is high) and add affiliate cards to more pages.
3. Expand colleges with net-price data (SFA files) and program-level pages if the niche shows traffic.
4. Weekly: update `docs/REVENUE.md`; prune or double down per data.
5. Keep pages <20k per deployment (ifsc 19.6k, places 19.2k, zip 17.8k near the cap — next growth
   needs a second project or a dynamic Worker).

## Known issues

- One duplicate title on colleges (two same-named institutions in one city) — cosmetic.
- Pincode project is the other agent's; our sources kept for reference.
- Ads show no fill at zero traffic; ad divs render empty.
- IFSC branch page has a harmless redundant sentence.
