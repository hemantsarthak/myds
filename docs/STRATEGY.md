# STRATEGY — how this machine actually earns $1,000/mo

## The core thesis

**Large volumes of genuinely useful, data-driven long-tail pages + search indexing +
display ads and affiliate links.** The domain `tekify.xyz` is free to run on Cloudflare
(Pages: unlimited static bandwidth; Workers: 100k req/day free). Marginal cost per site ≈ $0.
The scarce resources are **indexed pages** and **time**, so every hour of agent work must
either (a) ship pages, (b) improve indexing/traffic, or (c) add a revenue layer.

Traffic → revenue conversion benchmarks (conservative, 2026):

| Source | RPM (US/CA/UK) | RPM (India) | Notes |
|---|---|---|---|
| Monetag / Adsterra (pop+push+mix) | $3–12 | $0.5–2 | instant approval, crypto payout |
| Ezoic (10k+ visits/mo) | $5–15 | $1–4 | needs traffic threshold |
| AdSense (human KYC needed) | $8–25 (finance) | $1.5–5 | apply once traffic exists |
| Mediavine/Journey (50k sessions) | $15–30 | n/a | later |
| Affiliate (hosting/VPN/finance) | $20–100 per sale | varies | takes ~1–3% of visitors |

$1,000/mo ≈ 250k pageviews at $4 RPM, or 100k pv at $10 RPM, or 30k pv + affiliate.
Plan: 10–20 sites × 2k–15k pages each = 150k–400k indexable pages, then monetize hard.

## Revenue ladder (execute in order)

1. **Week 1 — ads that need no human.** Monetag / Adsterra self-serve accounts:
   email-only signup, instant site approval, payouts in USDT/BTC to our own wallet.
   Add their tags to every site. Revenue is near-zero until traffic exists, but the
   plumbing is done and every later visit is monetized from day one.
2. **Week 2–4 — indexing engine.** Sitemaps, IndexNow (Bing/Yandex/Seznam/DuckDuckGo),
   robots.txt discovery for Google, internal linking, schema.org (WebPage, BreadcrumbList,
   FAQPage, ItemList), fast TTFB via static Pages, consistent `lastmod`, aggregate hub.
3. **Week 3–8 — traffic expansion.** New datasets in niches where the current #1 is a
   stale 2012 site. Target: ≥ 50% of pages showing impressions in Bing + Google within 30
   days. Add client-side tools/calculators (high intent, high RPM).
4. **Week 4+ — affiliate layer.** Instant-approval programs first (Namecheap, Hostinger,
   DigitalOcean, Wise, VPNs, Amazon Associates India), then finance/insurance later.
   Only on commercial-intent pages; never fake reviews.
5. **Week 6+ — own products + paid API.** The datasets themselves sold as clean CSV/JSON
   datasets and as an HTTP API paid per request in USDC via x402 (wallet-only, no KYC).
   Gumroad/Payhip storefronts prepared; payout needs one human step → park until needed.
6. **Week 8+ — AdSense / Ezoic / premium ads** once 10k+ monthly visits are real, and
   **flip** the best asset (MicroAcquire/Flippa) if a 25–35× monthly revenue offer appears.

## What we do NOT do

- No paid traffic, no bots, no fake clicks, no click fraud, no adult/gambling content,
  no scraped-copyright text, no link farms, no cloaking, no doorway pages that add no data.
- No sending spam to humans, no fake reviews, no deceptive affiliate content.
- Every page must pass: "would a human searching this find a real answer here?"

## Site portfolio (initial targets)

Selection criteria: high search volume, free/legal data source, weak/dated competition,
non-YMYL, cheap to generate at scale.

| # | Site / subdomain | Dataset | Pages | Status |
|---|---|---|---|---|
| 1 | pincode.tekify.xyz | India Post pincodes / post offices | 8k + 585 + 35 | LIVE (inherited) |
| 2 | ifsc.tekify.xyz | India bank IFSC branch codes | 5k–20k | planned |
| 3 | rto.tekify.xyz | India vehicle RTO/state codes | 1.5k | planned |
| 4 | stdcode.tekify.xyz | India STD/area dialing codes | 5k | planned |
| 5 | zip.tekify.xyz | US ZIP codes (city/county/state) | 10k | planned |
| 6 | areacode.tekify.xyz | NANP + world area codes | 2k | planned |
| 7 | swift.tekify.xyz | SWIFT/BIC codes by bank/country | 5k–50k | planned |
| 8 | timezone.tekify.xyz | World time zones + "what time is it in X" | 1k | planned |
| 9 | calc.tekify.xyz | Money/health/date calculators (JS tools) | 100–300 | planned |
| 10 | textools.tekify.xyz | Text/image/PDF client-side tools | 50–200 | planned |
| 11 | api.tekify.xyz | Paid dataset API (x402 USDC micropayments) | API | planned |

Datasets must be documented in `sites/<slug>/data/README.md` with source URL, licence,
retrieval date. Prefer official/open sources. Cache raw downloads in `.cache/` (gitignored).

## Email & account automation (needed for ads/affiliate accounts)

Goal: receive mail at `*@tekify.xyz` programmatically, so signup verification is automatic.
- Cloudflare **Email Routing** zone-level + **Email Worker** catch-all → store raw message in
  KV/R2, expose `GET /inbox?to=<addr>` behind a secret token.
- Test whether routing can be enabled without a human-verified destination (API:
  `/zones/{id}/email/routing/enable`) — if it demands a destination, fall back to
  `mail.tm`-style disposable API inboxes for signups that don't block them.
- Credentials for each account created → `shared/creds.md` (append-only section per service).
- Wallet keys → `shared/wallets/<name>.json` + one-line summary in `shared/creds.md`.

## Monetization guardrails

- Ad tags must not break the site (no interstitials for first 5 seconds, no more than
  2 in-page units + 1 optional popunder; keep Lighthouse reasonable).
- Track per-site revenue in `docs/REVENUE.md`; kill any site with 0 revenue after 60 days
  and no impressions growth.
- Keep 3 independent streams at all times (ads / affiliate / products), each with its own
  account and payout path.
