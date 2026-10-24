# REVENUE — ledger

Every verified revenue event and every payout. Amounts in USD. Sources: display ads,
affiliate, product sales, API, site sale. Update at least weekly.

## Totals

| Month | Gross | Payouts received | Net | Notes |
|---|---|---|---|---|
| 2026-10 (partial) | $0.00 | $0.00 | $0.00 | pre-traffic; infrastructure + tags live |

## Ledger

| Date | Source | Site | Amount | Status | Notes |
|---|---|---|---|---|---|
| 2026-10-22 | HilltopAds | all sites | $0.00 | live tags, no traffic yet | account 409868, site 925719, zones 7541137 (in-page push), 7541153 (banner 300x250), 7541169 (popunder) |
| 2026-10-22 | Travelpayouts | airports + hub | $0.00 | approved, cards live, no traffic yet | 15 tracked links; flights/eSIM/compensation cards on 10,179 airport pages |

## Payout accounts

| Service | Method | Destination | Terms | Status |
|---|---|---|---|---|
| HilltopAds | crypto (BTC / USDT-TRC20), PayPal, Paxum, Wise, wire | wallet — paste address in My Account → Payment system when balance approaches $20 | min $20, weekly Tue, Net7 | LIVE, no balance yet |
| Travelpayouts (137 travel brands) | PayPal / wire / Payoneer | add payout method in dashboard when balance > $50 | min $50, 30-day cookie, partner 764877 marker 793747 | **APPROVED** — cards live on airport + hub pages; no balance yet |
| Hostinger affiliates | PayPal | — | min $100 + 3 sales | submitted, manual review |
| Cuelinks (India) | Indian bank | — | ₹500 | email confirmed, channel verify pending |
| Monetag | — | — | — | blocked: one reCAPTCHA solve needed (human, optional) |
| Adsterra | — | — | — | blocked: Cloudflare Turnstile (human, optional) |

## Live verification — 2026-10-23 03:40 IST (human asked "any income yet?")

Both money sources were read **directly from their dashboards/APIs**, not inferred:

| Source | Live reading | Method |
|---|---|---|
| HilltopAds (account 409868) | **Publisher Balance 0.00 USD**; all 5 zones `STATUS_ACTIVE`, `trafficStatus: unknown` (no traffic delivered yet); website `tekify.xyz` (925719) approval still `STATUS_APPROVAL_PENDING` | panel HTML (session cookies) + GraphQL `zones(siteId: 925719)` |
| Travelpayouts (partner 764877) | **balance usd `0`**, next payout `0`, payments `[]`, actions `count 0` | `GET https://api.travelpayouts.com/finance/v2/get_user_balance` with header `X-Access-Token: <api_token>` (also `get_user_next_payout`, `get_user_payments`, `get_user_actions_affecting_balance`) |
| Edge traffic (2 days) | 55,092 requests, **0 human sessions**: ClaudeBot 27,684 + Anthropic 340 (~51%), UA-rotating crawler 20,700 (~38%), scanners 3,664; Googlebot **6**, Bingbot **30** | `python scripts/traffic.py --days 2` |

**Conclusion: total income to date = $0.00.** Not a setup failure — the ad tags are live and serving
(`unfoldedtrade.com` scripts on pages), but display ads need human impressions and affiliate needs
human clicks, and there is still no human traffic. First dollar depends on search indexing.
Re-check cadence: Hilltop website moderation 24–48 h from 2026-10-22; re-read both balances weekly.

**Re-check 2026-10-24 17:15 IST — still $0.00.** HilltopAds balance `0.00 USD` (409868),
Travelpayouts balance `0` / 0 actions / no payments. Edge logs now show **Googlebot 2,020 requests
in 48 h** (was 6 on 10-23): Google has started crawling the sitemap URLs — discovery happening,
no rankings or impressions yet. ClaudeBot 83,586 requests in 48 h is the dominant crawler.

**2026-10-24 17:55 IST — Google indexing has started (still $0.00).** `site:` queries show real
results on tekify.xyz, ifsccodes, zipcodes, airportcodes (about/guides/privacy pages plus real data
pages: *IFSC Codes in SURAT*, *ZIP Codes in North Dakota*, *Polokwane Airport (PTG)*). Bing still
0 indexed. No human sessions yet → no ad impressions/clicks → no revenue. Watch the self-hosted
counter/hilltop balance daily from here: the first $0.01 needs one human impression on an indexed page.

**Daily check 2026-10-24 21:00 IST — still $0.00.** Hilltop `0.00 USD` (no traffic delivered),
Travelpayouts `0` / no actions / no payments. Index coverage (Google `site:` sample): deep pages
indexed on **nursinghomes, homehealth, hospitals** (facility/agency pages), dialysis partial
(about + one state page), **healthinsurance not yet** (launched 10-24). New monetization:
**Infolinks applied** (publisher id 3448908, contextual text ads, review ≤2 business days) — tag
live on hub + insurance + four health sites; no impressions until approval.

## Milestones

- [ ] $1 first revenue
- [ ] $10/mo
- [ ] $100/mo
- [ ] $1,000/mo (target)

## Traffic baseline (self-hosted counter)

`python scripts/ops.py stats --site all --days 7`

| Date | Pageviews | Notes |
|---|---|---|
| 2026-10-22 | ~0 human / 326 crawler renders | 7 properties live, 72,776 sitemap URLs; Googlebot/Bingbot rendering pages (airport 139, zip 116, ifsc 69, places 2) |
| 2026-10-22 (evening) | 0 | colleges.tekify.xyz launched (6,056 pages); IndexNow accepted |
