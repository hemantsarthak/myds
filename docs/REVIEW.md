# REVIEW — independent audit, 2026-10-22

> Written by the Team Lead (DSH web session) after auditing the repo, the live sites and
> the analytics between 19:00–19:30 IST. Treat it as a second opinion, not a replacement
> for `docs/STATE.md`. Read together with `docs/STRATEGY.md`.

## Snapshot (verified live during the audit)

- 11 properties, 113,451 sitemap URLs. All homepages HTTP 200, TTFB 0.27–0.29 s,
  Cloudflare compression on. Pages are ~2–3.5k chars of visible text, 10–17 KB HTML.
- Every page has canonical, JSON-LD (BreadcrumbList/WebSite/ListItem), robots meta,
  `robots.txt` + sitemap, 3 HilltopAds scripts, 1 analytics beacon, 11-site footer network.
- Data quality is real: ZIP 90210 (pop, county, area codes, nearby ZIPs), WGU (net price,
  retention, tuition), nursing homes (CMS stars), all sourced from public datasets.
- Revenue: $0.00. Human traffic: ~0 (the counters' "views" are our own test loads).
- Indexing evidence (updated 19:30 IST): the **Cloudflare edge census** now in `docs/TRAFFIC.md`
  (33,264 requests / 48 h) shows **Googlebot 0, GPTBot 0, Bingbot 15, Applebot 4, ClaudeBot
  14,207**. Google's only touch on the domain is a Safe Browsing check — it has not fetched the
  pages at all. This is a **discovery** problem, not a ranking problem. Round-12's `site:` = 0
  is consistent with that. The JS analytics "bot" counts in `ops.py stats` are polluted by
  synthetic test hits and must not be used as crawl evidence (the JS counter reported GPTBot
  hits while the edge saw zero GPTBot requests). IndexNow "accepted" is only an acknowledgement.
- The self-hosted analytics is JS-only, so it **cannot** see a plain Googlebot/Bingbot fetch.
  Bot counts in `ops.py stats` are JS-executing agents plus synthetic tests — do not treat them
  as proof of crawl coverage. Only Search Console / Bing Webmaster Tools can prove indexing.

## What is genuinely good (do not throw away)

1. Infrastructure and automation: 11 deploys, daily GitHub health job, autonomous inbox,
   `ops.py` CLI, session-import for logged-in services. This is the hard part and it works.
2. The data pipelines are honest: federal/open datasets, licences recorded, Pages are
   deterministic and reproducible. That is a defensible long-term asset.
3. Monetization plumbing exists end-to-end (HilltopAds zones serving, Travelpayouts tracked
   links, wallet addresses). When traffic arrives it is already monetized.
4. Docs are thorough and the write-up discipline is rare. Keep it.

## Page-level findings (spot-check, 2026-10-22 19:20 IST)

Verdict scale 1–5 = "would a searcher choose this page over the current SERP".

| Site | Sample | Verdict | What is missing |
|---|---|---|---|
| calculators | `mortgage-payment/` | 4/5 | Working JS, formula, worked example, mistakes, FAQ — the only genuinely competitive page type |
| hospitals | `hospital/poplar-bluff-...` | 3/5 | No Care Compare link, no inspection dates, no map |
| nursing homes | `nursing-home/nspire-healthcare-plantation` | 3/5 | Ratings + staffing only; missing inspection dates, deficiencies, fines — the decision data competitors rank on |
| home health | `agency/complete-care-home-health...` | 2.5/5 | Many agencies render "Not rated" → hollow at scale |
| colleges | `college/harvard-university/` | 2.5/5 | IPEDS 2023 vs competitors' 2026 cycle; no median earnings, deadlines, peer comparison |
| area codes | `area-code/205/` | 2.5/5 | No live clock, map, who-called/spam, NXX prefix registry (3 of 5 real intents missing) |
| IFSC | `/ifsc/INDB0000858/` | 2/5 | Complete answer but phone is plain text, no bank/RBI link, no source/date, SWIFT "—" |
| ZIP | `/zip/90210/` | 2/5 | 245 words vs 3,984 on zip-codes.com; no ACS income/home-value/age, map, schools, **0 outbound links** |
| airport codes | `/airport/MGP/` | 1/5 | 38% of the page is 3 repeated affiliate blocks on a PNG airstrip with no scheduled service |
| places | `/place/anton-tx/` | 1/5 | Population/county/coords only; "Where is X?" is a fixed sentence with two slots |

Hard numbers from the audit: **7 of 10 page types have zero outbound links** to an authority;
no page has a map; JSON-LD is only `BreadcrumbList`/`WebSite` everywhere — **FAQPage = 0** although
every page renders an FAQ; `tel:` exists only on the three health types. Strip digits and proper
nouns and **98.8–100% of main-text tokens are identical across pages of the same type** (unique
prose = 1–3 sentences, ~40–70 words). All 113k URLs claim `lastmod` 2026-10-22 and no page shows
a data date or source line. `/about/` says "run by an automated publishing system" with no
methodology, named author, retrieval dates or error-reporting path; IFSC `/about/` claims 183,214
branches while 19,511 pages are published.

Competitor baseline: zip-codes.com ZIP 90210 = 3,984 words, 18 charts, map, "Data Last Updated:
October 1, 2026", per-metric Census citations; 24timezones.com area code = map + live clock;
nursinghomerating.org shows "most recent inspection 03-04-2026, 219 days ago". Consequence: a
Google crawl will mostly end at **"Crawled – currently not indexed"** — volume is not the
bottleneck, per-page completeness and authority are.

## Technical findings (second pass — live crawl of all 11 hosts)

Verified good: all hosts 200, brotli, correct 301 http→https (path preserved), real 404s,
canonical host, `index,follow`, one `h1`, `lang`, viewport; robots.txt + sitemaps fine on all;
sitemap counts match the deployed pages (they do **not** match `docs/SITES.md` — see below);
IndexNow key file live. Sitemaps are single `<urlset>`s, all < 20k URLs. The edge census also
confirms scanners probing `/.env*`, `/.git/*`, `config.json` get 404/403 — nothing exposed.

Critical:

1. **Sitemap-only orphans.** `sites/zip/build.py` caps city pages at 700 and state pages link
   only to cities, never to ZIP pages. Of 25 sampled ZIP pages, **10 had no city page** and
   **8 had no internal link path at all** (e.g. `/zip/05620/`, `/zip/73443/`). Those pages are
   discoverable only via the sitemap — on a 2-day-old domain, effectively never.
2. **200-link cap on state pages.** 28 of 53 nursing-home state pages sit at exactly 200 entity
   links; all state pages emit **7,708 links for 14,690 facilities**. Same for home health
   (5,293 links / 12,409 agencies) and places (2,695 / 16,000). Most entity pages have no
   internal entry point either.
3. **The index-check tooling is broken.** `scripts/search.py "site:example.com"` (control)
   returns unrelated Indian sites; SearXNG ignores the `site:` operator and the script reports
   "N results" as success. Bing via `web_fetch` returns query-agnostic results; DDG returns a
   captcha. So any future "we are indexed / competitors don't rank" conclusion from this tool
   is noise. Only round-12's real-Chrome Google check is credible, and only Search Console can
   replace it.

High/medium:

4. `lastmod` is fake-uniform: every URL in all 11 sitemaps is `2026-10-22`
   (`engine/sitegen.py` defaults `lastmod=today()`), so every rebuild restamps 113,456 URLs.
   Google will ignore it.
5. No entity schema: only `WebSite` + `BreadcrumbList` on every page; no
   Hospital/MedicalOrganization/CollegeOrUniversity/Place/FAQPage even where the HTML exists.
6. Thin/JS-only pages are inside the sitemaps: `/search/` is in 8 sitemaps and renders
   "Loading index…" without JS; body-text minimums: calculators 243 chars, hospitals 352.
7. `docs/SITES.md` is stale: lists 8 of 11 properties, says "113,451 pages / 79.7k URLs" while
   its own rows sum to 79,730; calculators 62 vs 67 live.
8. `ads.txt` 404 network-wide (HilltopAds does not require one, but a future network will).
9. No edge HTML cache (`cf-cache-status: DYNAMIC`); deep TTFB 0.28–0.69 s vs 0.12 s home.
10. ZIP homepage `<title>` is double-escaped (`&amp;amp;` → "&amp;" in the SERP); deep titles
    run 76–83 characters (truncated in SERPs).
11. `www.tekify.xyz` is NXDOMAIN; ads also render on the 404 page.

## The three structural problems

### 1. The revenue math does not close in 30–90 days

Display ads on directory/lookup pages pay roughly **$1.5–3 RPM** (US/CA/UK; less for India).
$1,000/mo therefore needs **350–650k pageviews/month** — the plan's own $4 RPM assumption
(250k) is optimistic for HilltopAds inventory.

A realistic new-domain directory curve:

| Month | Indexed share (optimistic) | Pageviews/mo | Revenue @ $2.5 RPM |
|---|---|---|---|
| 1 | <10% | ~0–1k | <$3 |
| 3 | 20–40% | 5–30k | $12–75 |
| 6 | 50–70% | 40–120k | $100–300 |
| 9–12 | 70–90% | 150–400k | $375–1,000 |

So the current portfolio is a **6–12 month $1k asset**, not a 30–90 day one. Either re-baseline
(first $100/mo by day 60–90; $1k by month 6–9) or change the monetization (see #3).
Promising the human otherwise is setting up a false failure.

### 2. Indexing/authority is the bottleneck, and more pages make it worse

113k near-template pages on a **2-day-old .xyz** domain, with a popunder ad on every page, is
exactly the profile Google's *scaled content abuse* policy targets. Indexing is selective, not
proportional: adding 400k pages does not add 400k indexed pages — it adds crawl load and lowers
the average quality signal. And Google is not even at the starting line: **zero Googlebot
requests in 48 h of edge logs** while ClaudeBot pulled 14.2k requests. Discovery and trust must
be earned before indexing can begin; 11 subdomains also split whatever authority the apex earns
(subdomains are separate sites to Google).

*Opportunity worth noting:* ClaudeBot is the only crawler ingesting the content, which means the
pages are candidates for AI-answer citations. Keep them factual, dated and citeable (and add an
`llms.txt` + a clean data page on the hub) — referral traffic from AI answers is a plausible
2026 channel even though it is not a revenue line yet.

What actually moves this: **Search Console** (measurement + URL inspection), **backlinks/real
citations**, and **visible quality** on a small set of pages. None of those were the focus of
rounds 1–13.

### 3. Monetization sits at the lowest-value end of the data

The data we hold can support $10–100 outcomes: senior-care placement leads (nursing homes, home
health), college enrolment/student-loan affiliates, local services on ZIP/city pages, finance
affiliates on calculators. Instead we monetize lookup queries with $1–3 RPM banners — and Google
AI Overviews is eating exactly those lookup clicks. The fix is not more ad networks; it is
**decision pages + affiliate/lead offers in 2–3 verticals**, where 20–30k pageviews/mo can beat
500k lookup pageviews.

## Top changes, ranked by expected impact on revenue

1. **Human unblock batch (one ~20-minute sitting, see checklist below).** Without Search
   Console you are blind; without Bing WMT you cannot submit the 113k URLs; without the GitHub
   token scope you cannot publish the data repo backlink. This is the single highest-leverage
   hour in the project.
2. **Freeze page production until one site proves indexing.** No new properties (drop
   `swiftcodes`, further airport expansion, more subdomains). Spend the same hours on
   differentiation and distribution instead.
3. **Fix the internal link graph.** Paginate the state/city lists (remove the hard 200-link cap
   and the 700-city cap), add A–Z and county/neighbourhood index hubs so every entity page is
   ≤3 clicks from `/`, and drop the JS-only `/search/` pages from the sitemaps (`noindex`).
   Without internal paths, a 2-day-old domain will never crawl 113k sitemap URLs.
4. **Pick 2 verticals and build the money layer**: senior care (nursing homes + home health +
   hospitals) and ZIP/local. Per the page audit: nursing homes need the decision data (inspection
   dates, deficiencies, fines, official Care Compare link) before they can outrank the current
   SERP; ZIP needs ACS demographics + map + a comparison block. Then attach the offers those
   verticals pay for (senior-care lead/affiliate, local services). Colleges and airport pages are
   long-tail-only (IPEDS 2023 is off-cycle for head terms; airport affiliate cards are off-intent).
5. **Backlinks program (the actual ranking lever).** (a) publish the prepared
   `tekify-open-data` repo + GitHub Pages landing (blocked on token scope); (b) ship 2–3
   embeddable widgets ("look up your ZIP/area code/IFSC") that carry a followed credit link;
   (c) publish 2–3 genuine data studies (e.g. *"US nursing-home staffing by state, 2026"*) and
   pitch local outlets/newsletters; (d) publish articles on Substack once the publication
   exists.
6. **Instrument before scaling — and fix the tooling.** Add GSC + BWT for indexing/impressions,
   keep `scripts/traffic.py` (edge census) as the crawl log — it already answers "who is actually
   fetching us" — and publish a weekly report: requests by crawler, indexed pages, impressions,
   clicks, CTR, avg position, revenue/site. Make "pages shipped" stop being a KPI. Also repair or
   retire `scripts/search.py`: its SearXNG tier ignores the `site:` operator and returns
   unrelated results while reporting success — any session that trusts it will draw false
   conclusions about indexing and competition. Until GSC/BWT exist, treat "indexed" as unknown.
7. **Kill the popunder** (and set HilltopAds to mainstream-only inventory). Popunder is
   UX-hostile, hurts Core Web Vitals and AdSense eligibility later, and unknown creatives can
   get the domain flagged by Safe Browsing — the one failure mode that kills the whole asset.
8. **Per-page completeness pass (highest SEO ROI after links).** For each page type: official
   record link + `tel:` on every phone + OSM static map from the lat/lon already stored +
   "compared with state/national" block computed from our own files + visible
   "Source: <dataset> <release date>, retrieved <date>" + `dateModified`/`FAQPage`/vertical
   schema + real sitemap `lastmod` (data release date, not build date). Delete the repeated
   affiliate blocks on airport pages; fix the IFSC `/about/` branch-count mismatch; add a
   methodology/about page naming a human owner. Rebuild only `sitemap.xml` + the changed
   templates, not all 113k pages, where possible. Fix the ZIP homepage `<title>` double-escape
   and over-long deep titles while in there.
9. **Close the small technical holes**: emit an `ads.txt` for HilltopAds; add `www.tekify.xyz`
   DNS + 301 to the apex; set an edge-cache-friendly `Cache-Control` for HTML in `_headers`
   (deep TTFB is 0.28–0.69 s, home 0.12 s); stop serving ads on the 404 page; refresh
   `docs/SITES.md` (it lists 8 of 11 properties and its page totals are wrong).
10. **Architecture limit**: Cloudflare Pages caps a project at 20k files. `ifsc` is at 19,590
    and `places` at 19,210 — both effectively full. Future growth needs a Worker-rendered
    site (R2/D1 data + cached HTML) or fewer pages, NOT more subdomain projects. Also consider
    consolidating future content into paths on fewer domains (authority concentration).
11. **Ops hygiene**: one writer at a time (a second session commit landed mid-audit — deploy
    races are real); exclude `.cache/`, `node_modules/`, `sites/*/site/` and
    `shared/chrome-agent-profile/` (~2.2 GB total) from OneDrive sync; rotate the PAT that is
    embedded in `.git/config`; remove `bottest`/`selftest` from analytics; trim `STATE.md`
    (273 lines of round history) into `STATE.md` (current, <80 lines) + `HISTORY.md`.
12. **Portfolio discipline**: define kill/keep criteria now (e.g. zero GSC impressions after
    60 days → stop investing; a property with clicks and a monetizable intent → double down).
    Current view from the page audit: **invest** `zipcodes` (weakest incumbent, exact-match US
    intent, ACS data already easy to add) and `nursinghomes` (highest CPC, 15k facility-name
    queries, dated scraper competition); **keep, don't expand** `ifsc` (largest raw volume but
    India RPM ~$1 and it duplicates the Minimax agent's `ifsc.tekify.xyz`), `hospitals`,
    `calculators` (small, high intent — expand after links), `places`, `areacodes`;
    **freeze** `airportcodes` (off-intent affiliate blocks) and college head terms (off-cycle
    data) — long-tail institution pages only. Consolidate future content as paths on fewer
    domains instead of new subdomains.


## Human unblock checklist (only these; ~20 min total)

| # | Action | Why it matters | Time |
|---|---|---|---|
| 1 | Create / log into a Google account in the **AI Agent Chrome** profile and verify `tekify.xyz` in Search Console (DNS TXT record — the agent can add it on request) | Only real indexing measurement; URL inspection; sitemap status | 5–8 min |
| 2 | Finish the Microsoft / **Bing Webmaster Tools** signup (the "press and hold" step), then hand the API key path to the agent | 10k URL submissions/day + index status + query data | 1–2 min |
| 3 | GitHub token: add **Contents: Read and write** for `tekify-open-data` (or all repos) | Publishes the dataset repo + GitHub Pages backlink | 2 min |
| 4 | Substack: complete the publication creation captcha | Publishes articles that link every directory (followed links) | 1 min |
| 5 | (Optional) approve a small budget for a `.com` domain once one niche proves itself | `.xyz` is a trust/approval handicap for ads and search | later |

Everything else in `docs/ADS.md` / `docs/AFFILIATE.md` (Monetag, Adsterra, CJS, Awin,
Cuelinks) is second-order until traffic exists — do not spend human time there yet.

## What NOT to do

- Do not apply to AdSense/Ezoic now (zero traffic + programmatic pages = likely rejection).
- Do not add more ad units or networks; the ceiling is traffic, not fill.
- Do not build `swiftcodes` / more subdomains / more pages before indexing is proven.
- Do not buy traffic, and do not use the popunder to "make something happen".
- Do not keep publishing round-by-round history into `STATE.md` (it is becoming token bloat
  for every future session).

## Success criteria for the next 30 days

1. Search Console + BWT live, weekly numbers in `docs/REVENUE.md`.
2. ≥ 1 property with ≥ 100 indexed pages **and** ≥ 100 impressions/week in GSC.
3. ≥ 3 real referring domains (not nofollow UGC).
4. Popunder off, every entity reachable by internal links (≤3 clicks), real `lastmod`,
   per-vertical schema + methodology shipped, `ads.txt` served.
5. First affiliate click tracked via `/go/` (even if $0 revenue).

If none of 1–3 happens by day 30, the model is wrong and the strategy should change (not the
page count).
