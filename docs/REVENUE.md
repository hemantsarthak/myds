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

## Milestones

- [ ] $1 first revenue
- [ ] $10/mo
- [ ] $100/mo
- [ ] $1,000/mo (target)

## Traffic baseline (self-hosted counter)

`python scripts/ops.py stats --site all --days 7`

| Date | Pageviews | Notes |
|---|---|---|
| 2026-10-22 | ~0 | counter wired ~15:00 IST; sites launched same day, indexing not yet started |
