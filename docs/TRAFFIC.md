# TRAFFIC — real edge traffic (Cloudflare zone analytics)

> Added 2026-10-22 ~19:25 IST. This is the measurement layer that was missing: it reads the
> zone's own HTTP logs, so it sees **every request that reached Cloudflare** — including plain
> crawlers and scanners that never execute JavaScript.

## Why this exists (and why `ops.py stats` alone is not enough)

`workers/analytics` is a JS beacon. It can only count clients that run JavaScript, so it is
**blind to plain Googlebot/Bingbot fetches, sitemap requests, `robots.txt` fetches and scanners**.
Worse, its bot counters are polluted by synthetic test hits committed in earlier rounds —
on 2026-10-22 the JS counter reported "GPTBot 142 hits" on zipcodes while the edge shows
**0 GPTBot requests** in the same window. Do not use `stats` bot numbers as evidence of crawl.

Use `scripts/traffic.py` for "who is actually hitting us" and reserve Search Console / Bing WMT
for "what got indexed and what ranking it has".

## Usage

```bash
python scripts/traffic.py                          # last 2 days: classes, crawlers, hosts, status
python scripts/traffic.py --days 2 --host zipcodes.tekify.xyz --top 10   # per-host + top paths
python scripts/traffic.py --json                   # machine-readable
```

Needs `CF_API_TOKEN` in `shared/.env` (same token as `ops.py`; it needs Zone Analytics: Read —
the current token already has it). Free-plan GraphQL keeps only a short window (~2 days of
`httpRequestsAdaptive` data); `--days 7` returns what is retained. UA strings are spoofable and
requests ≠ pageviews (a page plus its assets is several requests), so treat this as a census of
*who is visiting*, not of sessions.

## Snapshot — 2026-10-22 19:25 IST, last 2 days, 33,264 requests

| Class (by UA) | Requests | Share | Notes |
|---|---|---|---|
| AI crawlers | 14,481 | 43.5% | **ClaudeBot 14,207** + Anthropic 274 |
| Browser-UA, unverified | 14,140 | 42.5% | no referrers, every host, lands on `/` — UA-rotating crawler/monitor, not humans |
| Scanners | 2,567 | 7.7% | LeakIX 1,503, `nginx-ssl early hints` 1,064 |
| Other | 1,689 | 5.1% | incl. `google-trust-services/2.0` (204, Google Safe Browsing check) and our own `tekify-health/1.0` (103, GitHub Actions) |
| Scripts | 358 | 1.1% | curl 297, headless Chrome 38 |
| Search engines | 19 | 0.1% | Bingbot 15, Applebot 4 |
| SEO tools | 10 | 0.0% | AhrefsBot |

Named crawler census: **Googlebot 0**, Google-InspectionTool 0, GoogleOther 0, GPTBot 0,
PerplexityBot 0, CCBot 0, Yandex 0, DuckDuckBot 0, PetalBot 0 · Bingbot 15 · Applebot 4 · ClaudeBot 14,207.

Status codes: 200 → 23,761 · 404 → 4,245 (scanners probing `/.env*`, `/.git/*`, `config.json` —
**nothing exposed**, they get 404/403) · 301 → 2,393 · 403 → 1,198 · 504 → 1,132 (all from the
`nginx-ssl early hints` probe, not real pages) · 522 → 91.

## What it means

1. **No humans and no Google.** Zero Googlebot requests in the window. The only Google-side
   touch is `google-trust-services` (Safe Browsing), i.e. Google knows the domain exists but is
   not crawling it. Combined with `site:tekify.xyz` = 0 pages, the conclusion is discovery, not
   ranking: Google never fetched the pages, so there is nothing to rank yet.
2. **ClaudeBot is the only crawler actually ingesting the content** (≈14.2k requests in 48h —
   it is chewing through the sitemaps). AI-search is the one channel currently reading us; it is
   not a revenue channel yet, but it is an argument for keeping pages clean, factual and
   cite-able (and for adding `llms.txt` / a public data page).
3. **The ZIP/places/airport "bot renders" in earlier notes were misleading.** They came from the
   polluted JS counter, not from real search-engine crawls.
4. **The site is being actively scanned for secrets** (`/.env`, `/.git/config`, `config.json`).
   That is normal internet background noise; the current answer is 404/403. Keep secrets in
   `shared/` (gitignored) and never inside a `site/` deploy directory.
5. **Watch item:** the moment Googlebot appears in `traffic.py`, indexing is about to start.
   Run it once a day; it is the earliest possible signal (GSC would show it later, and only if
   the human does the Search Console step).

## Related

- `docs/REVIEW.md` — independent audit (page quality, revenue math, what to build next).
- `docs/ANALYTICS.md` — the self-hosted JS beacon (human pageviews only).
- `scripts/ops.py stats` — JS beacon numbers; treat views as *rendering* clients, not traffic.
