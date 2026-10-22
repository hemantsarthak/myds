# ANALYTICS.md — self-hosted pageview counter

The Cloudflare API token on this account has **no Web Analytics (RUM) permission**, so we had
no traffic measurement at all. This is our own cookie-free pageview counter on the same
Cloudflare account, built on the proven pattern of `workers/mailbox/`: one Worker + one KV
namespace + a token-protected JSON read API.

```
browser -> GET https://analytics.monetec2.workers.dev/e.js?site=ifsc
        -> beacon GET /hit?site=ifsc&p=/110001/&r=google.com&t=Title   (1x1 gif)
        -> hits aggregated in Worker memory -> flushed to KV as immutable daily shards
        -> GET /stats?token=...&site=ifsc&days=7                       (JSON)
        -> python scripts/ops.py stats --site ifsc --days 7            (human readable)
```

## Add the tag to a site

```python
from engine.analytics import analytics_tag

extra_head = analytics_tag("ifsc")   # '<script defer src="https://analytics.monetec2.workers.dev/e.js?site=ifsc"></script>'
```

- `engine/analytics.py` is the ONLY place the snippet lives (mirrors `engine/ads.py`).
- Base URL comes from `ANALYTICS_URL` (`shared/.env`), default
  `https://analytics.monetec2.workers.dev`.
- `site_slug` must match the slug used when reading stats (lowercase letters/digits/hyphen).
- The beacon sets no cookies, does no CORS, and only reports: current pathname, referrer
  **hostname** (internal `tekify.xyz` referrers are dropped), and page title (title is received
  but not stored — it is not needed for counting).
- One hit fires immediately per page load. Client-side route changes in an SPA are not counted
  (Pages sites here are static, so irrelevant).

## Read stats

```bash
python scripts/ops.py stats --site ifsc --days 7          # totals, per-day, top pages, referrers
python scripts/ops.py stats --site ifsc --days 1          # today (UTC)
python scripts/ops.py stats --site all --days 7           # every site with traffic
python scripts/ops.py stats --site ifsc --day 2026-10-21  # a specific UTC day
python scripts/ops.py stats --site ifsc --json            # raw JSON for scripts
```

Either `ANALYTICS_TOKEN` (Worker secret) in `shared/.env`; the CLI adds it as `?token=`.
Equivalent HTTP:

```
GET /stats?token=…&site=ifsc[&day=YYYY-MM-DD][&days=N][&top=N]
GET /stats/all?token=…
GET /health            (public)
```

Response: `{site, range:{from,to}, days:[{day,views,bots,shards}], totals:{views,bots},
top_pages:[{path,views}], top_referrers:[{referrer,views}], shards, distinct_paths,
distinct_referrers, generated_at}`. `views` excludes bots; bots are counted separately.
`top=0` skips fetching shard bodies (metadata-only totals, cheapest read pattern).

## Storage model (why it is not one counter key)

KV free tier: **100k reads/day, 1k writes/day**. A naive "increment a KV counter per hit"
would burn the account's entire write budget in 1000 pageviews. Instead:

- Hits are aggregated **in Worker isolate memory**.
- A flush writes one **immutable shard key**:
  `s:<site>:<day>:<flush-ms>:<rand>` → `{views, bots, paths:{…}, refs:{…}}`
  with KV metadata `{site, day, views, bots}` and a 90-day TTL.
- No read-modify-write and no shared counter key → concurrent isolates can never overwrite
  each other's numbers; stats simply sum shards.
- `/stats` reads shards via KV `list` for the requested day(s): totals come from list
  metadata, top pages/referrers from shard bodies. `/stats/all` is metadata-only.
- Per-shard cardinality caps: 200 distinct paths / 100 referrer hosts (overflow → `"(other)"`).
  `/stats` top lists are capped at `top` (default 20, max 100).

### Flush triggers (each flush = 1 KV write)

1. **First hit on a cold isolate** — persists immediately (so single-page visits are never lost).
2. **≥ FLUSH_HITS (50) buffered hits** — busy traffic batches.
3. **Deferred flush ~20 s after a hit**, scheduled via `ctx.waitUntil()` — captures the tail of
   a visit (hits after the first page). *Note: a plain module-level `setTimeout` does NOT run
   after the response in Workers — verified, it silently loses data. Only `ctx.waitUntil()`
   keeps the work alive.*
4. **A hit ≥ FLUSH_MS (5 min) after the last flush** — low-traffic safety net.
5. **Every `/stats` request flushes pending hits first** — stats are current.

### Write budget analysis

Writes/day ≈ (cold starts) + (deferred visit-tail flushes) + (views/50 batches) + (stats calls),
hard-capped at `MAX_FLUSH_PER_DAY=600` (leaves ~400 writes/day for the mailbox worker on the
same account). Estimates for one active site:

| Pageviews/day | Typical flushes/day | Share of 1k budget |
|---|---|---|
| 100 | ~50–120 | 5–12% |
| 1,000 | ~150–350 | 15–35% |
| 10,000 | ~400–600 (capped) | 40–60% |
| 50,000+ | capped at 600 → undercount, upgrade to D1 | 60% |

Read budget: a `/stats` query = 1 KV `list` per day scanned + 1 `get` per shard on that day
(e.g. 7 days ≈ 7 lists + a few hundred gets). `/stats/all` = 1 list per 1000 shards. Typical use
is a handful of queries/day, orders of magnitude below 100k reads.

**Data loss tradeoff (accepted and documented):**
- Buffered hits are lost if the isolate is evicted before its flush — e.g. hits 2..n of a visit
  when traffic stops abruptly, or after a deploy. First pageview of a visit is always persisted.
- Once the 600/day write cap is hit, further flushes are deferred and can be lost. At that point
  the right fix is D1 (5M reads, 100k rows written/day free): swap the storage helpers
  (`flush`, `listKeys`, `sumShards`) — the API surface stays the same.
- KV is eventually consistent (≤ ~60 s global); stats may briefly lag a flush. Same-colo reads
  are immediate.
- No cookies / no unique-visitor metric (pageviews + bots only); UA-based bot detection;
  JS-only so most crawlers are never counted.

## Ops

```bash
python scripts/ops.py analytics-deploy          # deploy Worker + set ANALYTICS_TOKEN secret
```

- Worker `analytics` → `https://analytics.monetec2.workers.dev`
- KV namespace `analytics-pv` (`5d063dabbc1644789a3e24289582fe12`)
- Secret `ANALYTICS_TOKEN` (agent copy `ANALYTICS_TOKEN` in `shared/.env`, recorded in
  `shared/creds.md`); rotate by editing `shared/.env` and re-running `analytics-deploy`.
- Configurable vars in `workers/analytics/wrangler.toml`: `FLUSH_HITS`, `FLUSH_MS`, `DEFER_MS`,
  `RETENTION_DAYS`, `MAX_FLUSH_PER_DAY`, `INTERNAL_DOMAIN`.
- Test commands: `GET /health`, `GET /e.js?site=test`, `GET /hit?...`, then `stats --site test`.
  Test pageview shards auto-expire after 90 days; delete manually if they clutter `/stats/all`.

## Fallback / upgrade path

1. **Cloudflare Web Analytics** — if the API token later gets the RUM permission, create the
   site with `python scripts/ops.py analytics --host <domain>` and wire `CF_ANALYTICS_TOKEN` in
   `engine/sitegen.py` (the hook already exists). This would give real-user metrics, but the
   current token returns an auth error, hence this worker.
2. **D1** — the recommended upgrade above ~50k pageviews/day (see note above).
3. Anything else (Plausible, Umami, GA) needs accounts/budget/human steps; not needed for
   relative traffic measurement and ad-network "we have analytics" requirements — this worker
   is enough to prove traffic and to fill the basic fields ad networks ask for.

## Verification (2026-10-22)

- `e.js` served (633 B) with correct site slug; `/hit` returns 1x1 gif; 120 browser hits + 6
  Googlebot-UA hits produced exactly `views=120, bots=6`, correct top pages/referrers.
- `/stats/all` lists the site from shard metadata; bad site → 400; no/bad token → 401.
- Deferred `ctx.waitUntil` flush verified: 3 rapid hits on a fresh isolate persisted as
  first-hit shard + visit-tail shard without any `/stats` call.
- Plain `setTimeout` flush verified NOT to run after the response (discarded; replaced by the
  deferred `ctx.waitUntil` path).
