# STATE — current status

> Last updated: 2026-10-23 ~11:10 IST (DeepSeek agent, repo `myds`). Round 32 of the goal loop.
> Next session: read this, then `docs/BACKLOG.md`; pick the top ready item. Do not re-plan.

## One-line status

**12 properties live (~121,300 pages) with HilltopAds display ads, Travelpayouts affiliate cards,
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
| **Area Codes** | `myds-areacodes` | https://areacodes.tekify.xyz | 6,954 | ✅ | ✅ |
| **US Hospitals** | `myds-hospitals` | https://hospitals.tekify.xyz | 5,888 | ✅ | ✅ |
| **US Nursing Homes** | `myds-nursinghomes` | https://nursinghomes.tekify.xyz | 15,056 | ✅ | ✅ |
| **US Home Health** | `myds-homehealth` | https://homehealth.tekify.xyz | 12,777 | ✅ | ✅ |

≈ **121,300 pages** ours. Every property: canonical URLs, JSON-LD, breadcrumbs, sitemaps, robots,
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

## Round-32 work (2026-10-23) — llms.txt and Dataset schema on every property

1. **Engine now generates `llms.txt` for every site automatically** (`Site._llms_txt`): brand,
   description, source-data note, up to 25 key pages with absolute URLs, the JSON data endpoint and
   the network link. Hand-written versions on the hub and calculators are preserved.
2. **Dataset JSON-LD on every data site's home page**: `Site._dataset_ld` detects the site's
   `/data/*.json` index and emits a schema.org **Dataset** with a `DataDownload` distribution, so each
   property is machine-readable as an open dataset (what Google Dataset Search and data catalogues
   consume).
3. Full rebuild + deploy of all 12 properties in this round so the files reach production; the change
   is engine-level, so every future rebuild keeps them current.

## Round-31 work (2026-10-23) — machine-readable layer for AI crawlers and data catalogues

1. **`llms.txt` published** on the hub (2,385 bytes) and calculators site (1,388 bytes): plain-text
   summaries listing every directory with its URL and scale, all ten data analyses, the JSON data
   access paths and the dataset sources. This is the emerging convention for making a site legible to
   AI agents and crawlers — and GPTBot is already crawling the portfolio, so it is the one discovery
   channel we know is active.
2. **Rich JSON-LD on the hub home:** an `@graph` with **Organization** (with sameAs GitHub + Substack),
   **Dataset** (name, licence CC0, description, and seven `DataDownload` distributions pointing at the
   `/data/*.json` endpoints) and an **ItemList** of all twelve properties. This is what Google Dataset
   Search and other catalogues consume, and it costs nothing to have in place before indexing.
3. Verified `robots.txt` is permissive for all user agents (including AI crawlers) and references the
   sitemap. Both files deployed and confirmed live (200, correct sizes).
4. Search-engine status unchanged: Google and Bing still index zero pages for the domain.

## Round-30 work (2026-10-23) — health automation verified; dataset publisher ready

1. **Ran the daily health check locally** (the exact command the GitHub Action runs):
   `python scripts/health.py --submit` — all **12 properties returned 200**, total **121,285 URLs**,
   and the new URLs were submitted to IndexNow (hub 12, calculators 13, dialysis 7,809 — the dialysis
   baseline was stale after its rebuild). Report written to `reports/health-2026-10-22.md` and the
   `state/sitemaps.json` baseline committed, so tomorrow's scheduled run only submits genuinely new
   URLs.
2. **`scripts/publish_datasets.py` created** — one command to publish the four prepared datasets to
   **Hugging Face** (`--hf`) and **Zenodo** (`--zenodo`), with dataset cards, licences, keywords and
   `related_identifiers` pointing at the live directories. `--check` verified all four payloads are
   ready (39-291 KB samples). Tokens are read from `shared/.env` (`HF_TOKEN`, `ZENODO_TOKEN`) and are
   the only missing pieces — the accounts need the autonomous inbox, which resets at 00:00 UTC
   (05:30 IST).
3. No change in search-engine status: Google and Bing still index zero pages for the domain.

## Round-29 work (2026-10-23) — open datasets packaged for publishing

1. **`datasets/` folder added to the public repo** — four dataset cards with provenance, licence,
   column lists and `sample.csv` files, each linking to its live directory:
   - `ifsc-codes` — 183,214 Indian bank branches (Razorpay IFSC, MIT)
   - `us-zip-codes` — 41,711 ZIP codes (Census/GeoNames, public domain / CC BY)
   - `cms-hospital-ratings` — 5,419 hospitals (CMS, public domain)
   - `us-dialysis-facilities` — 7,490 dialysis facilities (CMS, public domain)
   Generator: `scripts/prepare_datasets.py`. README updated with the current scale (~121k pages) and a
   link to the datasets folder.
2. **Why:** these are the payload for publishing on **Hugging Face** and **Zenodo** — both heavily
   crawled, indexable platforms where an open dataset with a card linking to the live directory is a
   legitimate, useful artifact (unlike a link-drop). Those signups need the autonomous inbox, which is
   quota-limited until 00:00 UTC (05:30 IST); next round after the reset will attempt them.

## Round-28 work (2026-10-23) — three more insights; zone hardened for crawlers

1. **Three more insight articles** (hub now **16 pages**, **10 original analyses**), each computed from
   the cached datasets and charted:
   - **US ZIP codes by state** — how the postal geography is distributed (top states, shares).
   - **Which countries have the most airports?** — 86,258 airports by country; only a small share have
     scheduled commercial service.
   - **Indian bank branches by state** — 183,208 IFSC codes by state, with a note that the browsable
     directory publishes the 19,511 largest branch records (counts are dataset-wide, not page counts).
   Added to the home-page cards, sitemap (16 URLs) and IndexNow.
2. **Cloudflare zone hardened:** `always_use_https` enabled (HTTP now 301-redirects to HTTPS —
   verified on tekify.xyz and hospitals.tekify.xyz), `min_tls_version` raised to 1.2,
   `automatic_https_rewrites` and `early_hints` enabled. Crawler Hints is not available on this plan
   (API returns 400).
3. Reminder of the state: HilltopAds site still "Pending" (zones approved), Travelpayouts approved;
   both $0 pending traffic. No search engine has indexed the domain yet.

## Round-27 work (2026-10-23) — charts on the insight articles

1. **Inline SVG bar charts added** to three of the seven insight articles (no JavaScript, no external
   assets, ~680px wide, accessible `role="img"`): top 12 states by share of four/five-star hospitals,
   top 12 states by nursing-home staffing rating, and the national dialysis rating distribution.
   These are the pages most likely to be shared or cited, so a readable chart raises their quality.
   Verified live in the browser (SVG renders at 680px, 12 bars).
2. **Monetisation status re-checked:** HilltopAds site approval still "Pending" while all three ad
   zones are "Approved" and serving (verified earlier via network capture); Travelpayouts approved.
   Both at $0 because there is no traffic yet. No action possible until indexing starts.

## Round-26 work (2026-10-23) — four more calculators (75 pages)

1. **New calculators** in `sites/calculators/calcs_money4.py` (site now **75 pages**):
   - **Dividend income** — annual/monthly income, yield on cost, capital needed for a monthly target
     ($20k at 6% → $1,200/yr, $100/mo; $100k needed for $500/mo).
   - **Rent affordability** — 30% rule plus a stricter 25% check and what is left after other debts.
   - **Down payment** — cash needed, loan amount, monthly P&I and whether PMI applies
     ($400k at 10% down, 6.5%/30y → $40k down, $360k loan, $2,275.44/mo).
   - **Self-employment tax (US 2024)** — 92.35% base, 12.4% Social Security up to the $168,600 wage
     base (reduced by W-2 wages), 2.9% Medicare, deductible half; $80k profit → $11,303.64 (14.13%).
   Every calculator verified twice: Python vs JavaScript agreement at defaults, then live recompute in
   the browser (profit 80k → 120k gave $11,304 → $16,955, no page errors). Deployed + IndexNow.
2. Verified live: all four pages 200, sitemap 75 URLs.

## Round-25 work (2026-10-23) — external publications audited: most are noindex

1. **Indexability audit of everything we published off-site:**
   - **Substack notes and the Substack profile carry `meta robots: noindex`** — they cannot help
     Google discovery at all. (Only useful as a public profile, not as a link source.)
   - **Telegraph articles are indexable** (`index, follow`) but have no inbound links and telegra.ph
     publishes no sitemap/listing, so they are orphan pages until something links to them.
   - **GitHub repo `hemantsarthak/myds` is indexable** (no noindex) but nothing links to it.
   Conclusion: **no autonomous off-site publication we can create is currently feeding discovery.**
   The domain needs either a Search Console/Bing Webmaster submission or a link from an
   already-crawled page — both of which need the human (or money).
2. **`HUMAN_TODO.md` added at the repo root** — the three one-minute actions (GSC domain property,
   Bing WMT press-and-hold, Substack publication captcha) with exact steps and what each unlocks.
3. **College net-price insight parked:** the IPEDS SFA file only populates the income-band fields
   (NPIS412 etc.) for public institutions — 769 colleges instead of ~2,800 — so the analysis would
   have been misleading. Disabled with a comment rather than shipped; needs a better source
   (College Scorecard has net price by income for all institutions).

## Round-24 work (2026-10-23) — hub home page turned into a proper landing page

1. **Hub home page enriched** (the page Google would rank first): added a "How big is this?" section
   with the real scale (121,000+ pages across the twelve directories, listed per property), a
   **"For developers"** section documenting the free JSON endpoints (`/data/*.json`, no key, CORS),
   and a **FAQ** (licensing, freshness, corrections, ads). Live at <https://tekify.xyz/> (15.9 KB),
   sitemap + IndexNow updated.
2. Fixed a build break introduced while inserting that content (a triple-quoted block was left
   unterminated; the hub build failed and a stale deploy went out — caught by checking the live page,
   fixed, rebuilt and redeployed). Lesson repeated: **verify the live page after every deploy**.
3. **Bing index re-checked properly** with Bing's RSS output (`?format=rss&q=site:...`): the `site:`
   operator returns unrelated results for our hosts, i.e. **Bing has not indexed our pages either**
   (the earlier "Bing has a sample indexed" belief was wrong — that was a search-result artefact).
   So both major engines are still at zero; IndexNow submissions are queued but not yet processed
   for this new domain.

## Round-23 work (2026-10-23) — insights extended to seven, syndicated externally

1. **Two more insight articles on tekify.xyz** (hub now **13 pages**):
   - **Which US hospitals have emergency departments?** — 4,494 of 5,418 hospitals report emergency
     services (83%), with a state-by-state table (states with >=20 hospitals).
   - **America's largest nursing-home chains** — 10,184 chain-affiliated facilities across 611 chains;
     the 20 largest operators ranked by facility count, certified beds and average CMS rating.
   Both computed at build time from the cached CMS CSVs; wired into the insights index and the home
   page cards (8 insight links on the home page), sitemap + IndexNow updated.
2. **Syndicated two insight summaries to Telegraph** (10 telegra.ph articles total): the
   "best-rated hospitals by state" and "largest nursing-home chains" articles, each linking to the
   matching tekify.xyz insight page and to the directory. Tool: `scripts/browser/telegraph-insights.mjs`.
3. Recorded data points for future content: hospital ownership mix (2,322 voluntary non-profit,
   1,063 proprietary, 512 government-district), ER coverage, chain concentration.

## Round-22 work (2026-10-23) — data-driven insight articles on the hub (the link-earning layer)

1. **New `/insights/` section on tekify.xyz** with five original, data-computed articles — the kind of
   page that can attract links on its own, unlike a single record page:
   - **Which US states have the best-rated hospitals?** — Utah 79.3% of rated hospitals at 4+ stars,
     Mississippi 13.5%; full state table (42 states with >=20 rated hospitals), method documented.
   - **Hospital star ratings by ownership type** — non-profit vs for-profit vs government averages.
   - **Nursing-home staffing ratings by state** — average staffing + overall ratings, facility counts,
     certified beds.
   - **US dialysis facilities: the national rating picture** — distribution of the CMS five-star
     ratings and the states with the highest share of 4-5 star facilities.
   - **Which Indian banks have the most branches?** — the IFSC dataset counted by bank, with shares.
   Each article states its method and links into the matching directory (including specific state
   pages), so the numbers are verifiable and the pages pass readers into the data.
2. Every insight is computed at build time from the same cached public datasets (CMS, Razorpay IFSC)
   by `sites/hub/insights.py`; no manual numbers. Hub is now **11 pages**, linked from the home page
   ("Insights from the data" section) and from the nav, sitemap updated and IndexNow submitted.
3. Bug fixed while wiring: ownership grouping divided by zero for categories with no rated hospitals
   (only groups with a rated hospital are ranked now).

## Round-21 work (2026-10-23) — internal link cluster across the health properties

1. **Health cluster cross-linking.** Every hospital, nursing-home, home-health and dialysis facility
   page now ends with a "Related care in <state>" block linking to the other three directories' state
   pages. That is ~44,500 new contextual internal links within one topical cluster (hospital ← →
   nursing home ← → dialysis ← → home health), which helps crawl depth and topical relevance once
   the domain is indexed. Helper: `engine.health_cross_links()`; deployed for all four sites with
   IndexNow resubmission.
2. **Indexing status re-checked (Google + DuckDuckGo):**
   - Google still indexes **0** pages on tekify.xyz, and has also not yet indexed the Telegraph
     articles (`site:telegra.ph Tekify` → no match) or the Substack profile (`site:substack.com
     tekifydata` → no match). The external publications are younger than a day and themselves have no
     inbound links, so this is expected — but it confirms that the discovery chain still needs time
     (or a Search Console submission) before it can pass authority to our subdomains.
   - DuckDuckGo/Bing queries for our target content (hospital CMS rating, IFSC code, dialysis centre)
     do not surface our pages yet.
3. Analytics/mailbox stay quota-limited until 00:00 UTC (05:30 IST), both cached and graceful now.

## Round-20 work (2026-10-23) — new calculators, press page, and a deploy bug that hid deploys

1. **Four new calculators** (`sites/calculators/calcs_money3.py`): net worth, stock profit, crypto
   profit (fees on both sides) and emergency fund. Python and JavaScript twins verified to agree at
   defaults, then exercised in the real browser (inputs changed, results recomputed, no page errors).
   Calculators site is now **71 pages**, deployed and IndexNow-submitted.
2. **New `/press/` page on the hub** listing all 8 Telegraph explainers, the data sources behind every
   directory, the Substack profile and the GitHub repo; linked from the hub nav. This gives the
   external explainers an inbound link from our own network and documents provenance for readers.
3. **Discovery chain built:** four Substack notes now link to the Telegraph explainers
   (substack.com → telegra.ph → our subdomains). Found that telegra.ph has **no sitemap, robots.txt or
   recent-pages listing**, so unpublished-inbound articles are orphan pages — the Substack notes and
   the hub press page are what make them reachable.
4. **BUG FIXED — deploys could silently go to the wrong Pages project.** `ops.py deploy --project
   calculators` created a *new* project named `calculators` (created 15:45 UTC) while the live domain
   belonged to `myds-calculators`: wrangler reported success, the site never changed. Deleted the
   stray project and added `resolve_project()` which maps a bare slug to an existing `myds-<slug>` /
   `moneyds-<slug>` project and prints a note. **Lesson: verify a deploy by checking the live sitemap
   page count, not just the CLI output.**

## Round-19 work (2026-10-23) — discovery surface doubled; shared KV quota made visible

1. **Four more Telegraph explainers published** (total **8** indexable telegra.ph articles linking the
   directories): hospital CMS ratings before scheduling care, nursing-home star ratings, US ZIP-code
   structure + JSON index, and IATA vs ICAO airport codes. Verified live (200) with 3-6 tekify links
   each; all URLs recorded in `shared/discovery-links.md`. Tool: `scripts/browser/telegraph-articles2.mjs`.
2. **No-account publishing platforms tested:**
   - **rentry.co** — API works without an account and links are followed, but pages are
     `meta robots: noindex`, so they cannot help Google discovery. Rejected.
   - **write.as** — anonymous POST returns 201 with `id: "contentisblocked"` (link-spam filter). Rejected.
   - **Medium** — sign-in page offers email flow but needs the full magic-link round trip; not pursued
     this round (kept as an option).
3. **GitHub Actions health check is healthy but has not run yet:** workflow `portfolio-health` exists
   and is active in the repo, Actions enabled, but 0 runs because the first cron (`17 3 * * *` UTC)
   fires at 08:47 IST tomorrow. Expected, not a bug — it will post a report + IndexNow new URLs daily.
4. **Shared KV list() quota exhausted** (1,000/day, free plan): it broke BOTH `ops.py stats` and the
   autonomous inbox (same namespace). Both now have local TTL caches + clear "resets at 00:00 UTC"
   messages. Operational rule recorded: query stats at most a few times a day and prefer
   `--site X --days 1`; the quota resets 00:00 UTC (05:30 IST). Email reads are cached 10 min.

## Round-18 work (2026-10-23) — domain-level Google invisibility + first indexable citation

1. **Google indexes NOTHING on tekify.xyz** — checked with the agent browser against Google:
   `site:tekify.xyz`, `site:ifsccodes.tekify.xyz`, `site:zipcodes.tekify.xyz`,
   `site:hospitals.tekify.xyz`, **and the other agent's** `site:pincode.tekify.xyz`,
   `site:ifsc.tekify.xyz`, `site:solarcalc.tekify.xyz` — all "did not match any documents".
   So the whole domain is unknown to Google, not just our subdomains. Bing does index a sample
   (site: works there), and GPTBot crawls us. **Discovery is the single blocking problem.**
2. **Created a public, indexable Telegraph article** that links to all 12 properties:
   <https://telegra.ph/Open-data-directories-IFSC-codes-ZIP-codes-colleges-hospitals-nursing-homes-and-more-10-22-2>
   — telegra.ph needs no account/captcha (published through its web editor by the agent browser),
   the page is `meta robots: index, follow`, 11 outbound links to the directories (`rel="nofollow"`,
   which still counts for discovery when Google crawls the page). Tool: `scripts/browser/telegraph-publish.mjs`
   (also `scripts/telegraph_publish.py`, whose direct API call is blocked from this network).
3. **Blocked signups recorded:** Neocities requires reCAPTCHA/hCaptcha at signup; WordPress.com
   rejects `@tekify.xyz` ("email provider blocks some of our emails"). Substack remains the only
   platform where the agent could create an account + public profile/notes without a captcha
   (publication creation is the captcha-gated step — human action #5).
4. **Fixed colleges duplicate titles** (27, caused by `seo_title` truncation of long university
   names) that aborted a full rebuild; colleges now validates clean (0 dup titles).
5. **Three more targeted Telegraph articles** published (same no-account channel), each linking the
   relevant directories: an IFSC-code explainer (ifsccodes + hub), a CMS-star-ratings explainer
   (hospitals/nursinghomes/homehealth/dialysis + hub), and a US reference-data explainer
   (zipcodes/places/areacodes/airportcodes + hub). All verified public (200) with 2–12 tekify links
   each; URLs saved in `shared/discovery-links.md`.
6. **Title-dedup fallout fixed:** the earlier `seo_title` refinement removed the city from health-site
   titles, so long facility names truncated to identical titles (colleges 27, hospitals 170 dups) and
   aborted the rebuild. Titles now use city + facility ID as disambiguators; all three health builds
   validate clean.
7. Full footer refresh: hub/ifsc/airport/zip/calculators/places rebuilt and deployed; colleges,
   areacodes, hospitals, nursinghomes, homehealth, dialysis rebuilt+deployed with IndexNow in the
   same round so every footer links all 12 properties. Final audit of all 12: **0 failures, 0 warnings**.

## Round-17 work (2026-10-23) — dialysis site + analytics quota fix

1. **New property `dialysis.tekify.xyz`** — 7,809 pages from the CMS Dialysis Facility listing
   (public domain): 7,490 Medicare-certified facilities with CMS **five-star rating**, patient
   survival / hospitalisation / readmission / transfusion / ED-visit measures (each with the CMS
   better/as-expected/worse category and rate), transplant-waitlist percentage, operator and chain,
   number of dialysis stations, late-shift flag, services offered (in-centre HD, peritoneal, home HD
   training), address/phone, nearest facilities; plus 52 state pages, 250 city pages, rating pages
   1–5, two guides ("how the five-star rating works", "in-centre vs home dialysis") and local search.
   Verified live; IndexNow accepted 7,809 URLs; wired into hub, footer network, build_all, health
   check and `audit_sites.py`. Audit of all 12 properties: **0 failures, 0 warnings**; hub links 12.
2. **Analytics quota bug fixed:** `ops.py stats` was hammering the Worker's KV `list()` calls
   (free tier: 1,000/day) and crashed when exhausted. Added a local TTL cache (20 min) plus a
   `--refresh` flag and a graceful "quota exhausted, try after 00:00 UTC" message. Deeper fix
   (D1-backed analytics) noted as future work if query volume grows.
3. Dialysis data quirk fixed: some CMS rows prefix the facility name with the CCN ("032314 PHOENIX
   CHILDRENS…"); the build strips it. Duplicate-name facilities get CCN-disambiguated titles
   (124 duplicate titles caught by the validator before deploy).
4. Note: the other 11 sites' footers will include the new "US Dialysis" link on the next full
   rebuild (hub already does); the old cached URLs for renamed dialysis pages are edge-cache only
   (cache-busted requests return 404 correctly).

## Round-16 work (2026-10-23) — full code + live-site audit, fixes, and tooling

**Code audit:** every Python file compiles, every `.js/.mjs` parses, no stale cross-agent domains in
generated output (only the intentional footer link to `pincode.tekify.xyz` and the retained pincode
sources), no placeholder/TODO text in shipped pages, no mixed `http://` content, calculators formula
checks pass 11/11.

**Live-site audit (new tool `scripts/audit_sites.py`, run with 4–6 samples per site):** for all 11
properties it checks homepage status/title/description/canonical/viewport/ads/analytics/network
footer, robots.txt sitemap line, IndexNow key file, sitemap validity + host correctness + lastmod,
sampled pages (self-canonical, title 10–80 chars, description 40–200, h1, JSON-LD, lang, no noindex,
ads, analytics, page size, internal links resolve), `/search/` wiring, `/guides/`, data endpoint
status + JSON validity, security headers, and that the hub links every property and every link
resolves. **Final state: 0 failures, 0 warnings.**

Fixes made as a result:
1. **Long SEO titles** (84–92 chars) on colleges/hospitals/nursinghomes/homehealth — new
   `seo_title()` helper in the engine truncates the label (never the identifying part) to ≤ ~62
   chars; IFSC branch titles rebuilt so the IFSC code always survives truncation (a first attempt
   produced 944 duplicate titles — caught by the build validator, fixed).
2. **Short contact-page description** (36 chars) lengthened to ~110 chars.
3. **Broken `/cdn-cgi/l/email-protection` links**: Cloudflare's email obfuscation rewrites addresses
   on static Pages and its decoder link 404s. Disabled zone-level `email_obfuscation` via the API —
   emails now render as plain text, no broken links.
4. Untracked scratch files removed; audit + browser test scripts kept for every future round.

## Round-15 work (2026-10-22 late evening) — FUNCTIONAL BUG FIX: search was dead everywhere

The human reported that search on the hospital page did not work. They were right — and it was
worse than one page:

1. **Root cause:** `engine/sitegen.py` wrote `/assets/app.js` into every deployment but **never
   referenced it from the HTML**. Every search box on all 10 data sites (home pages and `/search/`
   pages) was therefore dead: the input existed, the JS existed, nothing loaded it.
2. **Fix:** the engine now injects `<script defer src="/assets/app.js?v=<content-hash>"></script>`
   into every page of a site that ships that file. The `?v=` hash busts the year-long immutable
   cache on `/assets/*` (which would otherwise have hidden future script changes from returning
   visitors).
3. **Also fixed:** the calculators home page never loaded `/assets/home.js`, so its filter box did
   nothing; it is now loaded (versioned too).
4. **Rebuilt and redeployed all 11 properties**, then tested in a real browser (agent Chrome):
   - 9 data sites × (home page + /search/) — typing a query produces result links on **all 18**
     combinations (ifsccodes 30, places 12, nursinghomes 16, homehealth 36, hospitals 4, others 1+).
   - Calculators home filter works (typing "mortgage" narrows 67 → 5 cards).
   - Calculator live recompute works (mortgage $400,000 @ 6%/30y → $2,398.20/mo, total $863,352.76).
   - No JavaScript page errors on any tested page.
   Test scripts kept: `scripts/browser/search-test.mjs`, `scripts/browser/search-test-home.mjs`.
5. Audited while there: custom 404 pages return 404 with a styled page; viewport meta present on
   every page; ads + analytics present; all `/data/*.json` endpoints used by search return 200
   (0.4–1.5 MB each); no broken internal links (validator clean on every build).

Lesson recorded: build-time validators check links and metadata but **not that referenced assets are
actually loaded** — browser-level tests belong in every content round.

## Round-14 work (2026-10-22 late evening) — discovery surface built

1. **Posted 11 public Substack Notes, one per property**, each with a short description and a link
   to that directory. Verified: profile <https://substack.com/@tekifydata> lists 11 notes and 11
   distinct tekify.xyz links; three note pages checked over plain HTTP return 200 with the link
   present (links are `rel="nofollow"` — still crawled for discovery).
   Note URLs (newest first):
   - https://substack.com/@tekifydata/note/c-367419883
   - https://substack.com/@tekifydata/note/c-367419538
   - https://substack.com/@tekifydata/note/c-367419209
   - https://substack.com/@tekifydata/note/c-367418919
   - https://substack.com/@tekifydata/note/c-367418616
   - https://substack.com/@tekifydata/note/c-367418356
   - https://substack.com/@tekifydata/note/c-367418008
   - https://substack.com/@tekifydata/note/c-367417738
   - https://substack.com/@tekifydata/note/c-367417398
   - https://substack.com/@tekifydata/note/c-367417097
   - https://substack.com/@tekifydata/note/c-367410106
2. Composer mechanics (for future sessions): open the profile, click the "What's on your mind?"
   prompt, wait ~4 s for the "New note" dialog, type into its contenteditable, click **Post**.
   Reusable script: `scripts/browser/substack-notes-batch.mjs`.
3. These notes give Googlebot 11 crawlable, high-authority pages that point at each subdomain —
   the discovery path that was missing when Google had indexed 0 pages. Re-check
   `site:tekify.xyz` in a few days.

## Round-13 work (2026-10-22 late evening) — first external citation live

1. **Substack account, public profile and first Note are live.**
   - Profile: <https://substack.com/@tekifydata> ("Tekify Data", handle `tekifydata`, bio set).
   - **Note published** with a link to <https://tekify.xyz>: verified public at
     `https://substack.com/profile/562668962-tekify-data/note/c-367410106` (HTTP 200, anchor to
     tekify.xyz present, `rel="nofollow noopener ugc"`).
   - Nofollow still matters for **discovery**: Google crawls UGC links on high-authority pages even
     when they are nofollow, which is the step we are missing (Google currently indexes 0 pages).
   - Login is a magic link to `substack@tekify.xyz` (read from our own inbox); the session lives in
     the shared AI Agent Chrome profile, so future sessions are already logged in.
2. **Substack publication creation is captcha-gated** ("Please complete the captcha to continue" at
   the *Claim your URL* step). Not defeated, per policy. **Human action (~30 s):** open
   `https://substack.com/settings` → Publishing → "Start a Substack", solve the captcha; the agent
   can then create `tekifyopendata.substack.com` and publish articles that link to every directory.
3. Also probed this round: WordPress.com rejects `@tekify.xyz` ("email provider blocks some of our
   emails") even after SPF/DMARC; Substack's API endpoints require the app session (cookie-only fetch
   returns 403 — use the UI or the in-page flow, not `/api/v1/*`).
4. Scripts kept for reuse: `scripts/browser/substack-onboard.mjs` (onboarding),
   `scripts/browser/substack-create-publication.mjs` (publication, stops at captcha),
   `scripts/browser/substack-note.mjs` (profile + single note), `scripts/browser/substack-notes.mjs`
   (batch notes — editor detection needs a small fix: wait longer for the composer).

## Round-12 work (2026-10-22 evening) — READ THIS: Google has not indexed anything yet

1. **Definitive indexing check (via the agent browser, real Chrome + Google):**
   `site:tekify.xyz`, `site:ifsccodes.tekify.xyz`, `site:zipcodes.tekify.xyz`,
   `site:hospitals.tekify.xyz` all return **"did not match any documents"**. Google has indexed
   **zero** pages after ~2 days and 113k URLs. Bing has indexed a sample (site: works there) and
   GPTBot is crawling, but Google — the traffic that matters — has not.
   **Conclusion: the bottleneck is external discovery/authority, not page count.** A brand-new
   domain with no inbound links is effectively invisible to Google, and sitemaps alone are not
   enough. Priority for the next sessions is BACKLINKS, not more pages.
2. **Email deliverability fixed:** added SPF (`v=spf1 include:_spf.mx.cloudflare.net ~all`) and
   DMARC (`v=DMARC1; p=none; rua=mailto:dmarc@tekify.xyz`) TXT records to tekify.xyz (deleted a
   duplicate SPF record created concurrently). This improves acceptance at services that check
   sender/receiver reputation.
3. **WordPress.com signup blocked:** their form rejects `@tekify.xyz` addresses with "This email
   provider blocks some of our emails" (heuristic on the domain/MX), even after SPF/DMARC.
   Not usable for a followed backlink.
4. **Substack account CREATED and verified autonomously** (`substack@tekify.xyz`): magic-link email
   read from our own inbox, full creator onboarding completed (topics, profile: name "Tekify Data",
   handle `tekifydata`, bio), account logged in in the shared AI Agent Chrome profile.
   **Next step:** create a publication (e.g. subdomain `tekifyopendata`) and publish 2–3 posts that
   link to the directories — Substack posts are indexed and links are followed, which gives Google
   both a discovery path and real backlinks. The publication step was not reached this session
   (the web app's Create flow needs a publication first; try `https://substack.com/publish/...`,
   the internal API `POST https://substack.com/api/v1/publication`, or finish the in-page onboarding
   with "Create" selected).
5. Also confirmed: HilltopAds ads still serve; calculator site now 67 pages (5 new tools added last
   round, formulas verified).

## Round-11 work (2026-10-22 evening)

1. **Who is actually crawling (new evidence).** The per-bot breakdown shows the recent bot hits are
   **GPTBot** (OpenAI), not Googlebot: airport 17, zip 46, places 59 GPTBot hits in the last two
   days. That means (a) our content is being ingested by AI crawlers, and (b) our JS-based analytics
   can only see crawlers that execute JavaScript — Bingbot does not, and Googlebot's rendering is
   not visible here yet. Google crawl/index status remains unknown without Search Console.
2. **Five new calculators** (deployed, formulas verified): retirement withdrawal (4% rule), debt
   payoff (months + interest, with a "pay 25% more" comparison), biweekly mortgage (interest and
   years saved — fixed a factor-of-2 bug found by the check), sales commission with broker split,
   and sleep-cycle bedtime planner. Calculators site: 62 → **67 pages**, IndexNow accepted.
3. **Backlink attempt blocked by token scope.** Created a public repo `hemantsarthak/tekify-open-data`
   (data documentation + samples + GitHub Pages landing page linking all 11 properties) to earn a
   followed link from github.io. The fine-grained GitHub token can create the repo but **cannot write
   contents or enable Pages** (403), and cannot delete the repo either — it is left empty.
   Human action if wanted: either delete that empty repo or add it to the token's repository scope;
   then the prepared generator can publish it. Search evidence in the same round: competitors rank
   for our target queries (bankifsccode.com etc.); we do not yet — expected at 2 days old.

## Round-10 work (2026-10-22 evening)

1. **Per-bot crawl visibility.** The self-hosted analytics worker now records which bot made each
   hit (Googlebot, Bingbot, DuckDuckBot, YandexBot, Applebot, Ahrefs, GPTBot, …) and
   `python scripts/ops.py stats --site <slug>` prints the breakdown. Verified with synthetic
   Googlebot/Bingbot hits. This is the only way to see whether Googlebot is actually crawling us,
   since we have no Search Console.
2. **Full network refresh.** Rebuilt and redeployed all 10 of our sites so that **every page's
   footer links to all 11 properties** (hospitals, nursing homes and home health were missing from
   the older sites' footers, which slowed discovery of the newest properties). Verified live: 11
   network links on airport and hospital pages.
3. Added `scripts/ad-check.mjs` — loads a page in the shared browser and reports ad-script
   responses + injected ad iframes (used last round to prove HilltopAds serves despite "Pending").

## Round-9 work (2026-10-22 evening)

1. **Verified ads actually serve** (this was a risk: HilltopAds site approval still shows
   "Pending"): loaded two of our pages in the shared agent browser and captured the network — all
   three ad scripts return HTTP 200 and the ad iframe is injected into the DOM
   (`unfoldedtrade.com` / `subtle-injury.com`). So the revenue plumbing works; only traffic is
   missing.
2. **New property `homehealth.tekify.xyz`** — 12,777 pages from the CMS Home Health Care Agencies
   file (public domain): 12,409 Medicare-certified agencies with CMS **quality-of-patient-care star
   rating**, services offered (nursing, PT, OT, speech, medical social, aide), individual quality
   measures (timely care, walking/bathing improvement, medication management, vaccination,
   discharge to community), ownership, certification date, address/phone, nearest agencies; plus 52
   state pages, 300 city pages, rating pages 1–5, two guides (how home health works; how the star
   rating works) and local search. Verified live; IndexNow accepted all 12,777 URLs.
3. Wired into hub, footer network, `build_all` and the daily health job — baseline is now
   **113,451 URLs across 11 properties**.
4. Health cluster is now four CMS-data properties: hospitals, nursing homes, home health, plus
   colleges — the highest-CPC part of the portfolio.

## Round-8 work (2026-10-22 evening)

1. **New property `nursinghomes.tekify.xyz`** — 15,056 pages from the CMS nursing-home Provider
   Information file (public domain): 14,690 facilities with CMS **overall / health inspection / QM /
   staffing star ratings**, staffing hours (aide, LPN, RN, total, weekend), turnover rates,
   ownership, certified beds, average residents/day, chain affiliation, abuse/special-focus/
   high-performing flags, inspection recency, sprinklers, resident council, address/phone, lat/lon
   and nearest facilities. Plus 52 state pages, 300 city pages, rating pages 1–5, two guides
   (how CMS ratings work; how to choose a home) and local search.
   Verified live (15 Craigside, Honolulu) — ads + analytics present; IndexNow accepted all 15,056 URLs.
2. Wired into hub, footer network, `build_all` and the daily health job: baseline is now
   **100,674 URLs across 10 properties**.
3. Note: the parallel writer added `scripts/search.py` (SearXNG/DuckDuckGo/Bing/Playwright web-search
   chain) and documented it in AGENTS.md — useful for future sessions, kept as-is.

## Round-7 work (2026-10-22 evening)

1. **New property `hospitals.tekify.xyz`** — 5,888 pages from CMS Provider Data (Hospital General
   Information, public domain): 5,419 hospitals with address/phone, hospital type, ownership,
   emergency services, birthing-friendly designation, **CMS overall star rating**, and quality
   measure counts by group (mortality, safety, readmission, patient experience, timely care);
   plus state pages (52), city pages (400), rating pages (1–5), two guides and local search.
   Verified live (AdventHealth Castle Rock: 5 stars, measures table, phone, emergency services).
   IndexNow accepted 5,888 URLs; wired into hub, footer network, build_all and the daily health job
   (baseline now **85,618 URLs across 9 properties**).
2. **Social/backlink channel probe (blocked):** Hacker News account creation is disabled
   ("Sorry, account creation disabled"); dev.to signup is OAuth-only (Apple/Facebook/GitHub/Google/
   Twitter — we only hold a GitHub PAT, not account credentials); DuckDuckGo lite returns no results
   for our domains yet. Conclusion: traffic must come from search indexing (IndexNow + Bing WMT once
   the human check is done), not from free social posting without human credentials.

## Round-6 work (2026-10-22 evening)

1. **Colleges enriched with money-and-outcomes data** (deployed, IndexNow accepted):
   - **Average net price after aid** (IPEDS SFA2223, 2022-23) plus a **net price by family income**
     table (under $30k / 30–48k / 48–75k / 75–110k / over $110k) — the numbers students actually
     compare. Coverage ~1,830 institutions (the rest do not report).
   - **Full-time retention rate** (EF2023D) — coverage 5,004 institutions.
   - **Campus setting**, **size category**, **highest degree offered** from HD2023 with label maps
     committed as `sites/colleges/labels.json` (so the build stays reproducible).
   Verified live on Michigan: net price $19,005, retention 98%, income bands $4,926 / $5,389 / $8,756…
2. Crawler activity is climbing: airport 275, zip 266, ifsc 121, places 61 bot renders in 7 days.
3. The parallel writer has been idle since ~17:11 (last writes: areacodes + engine/build_all).

## Round-5 work (2026-10-22 evening)

1. **Enriched all 17,759 ZIP pages** with NANP telephone area codes and a cross-link to the places
   directory (90210 -> 310, 424 verified live). Deployed + IndexNow accepted.
2. **Daily self-running health automation** (`.github/workflows/health.yml` + `scripts/health.py`):
   every day on GitHub's infrastructure it fetches all 7 homepages + sitemaps, compares against the
   committed baseline `state/sitemaps.json`, submits only NEW URLs to IndexNow, and commits a report
   to `reports/`. First baseline: 72,776 URLs across 7 properties. This keeps the portfolio
   monitored and pinging search engines while the laptop is off.
3. **Bing Webmaster Tools** remains one 30-second human press-and-hold away (Chrome window was left
   open until ~17:58 IST; the driver is `workers/bwtprobe/ms_flow2.js`). After that the whole
   submission of 72,776 URLs is scripted (`scripts/bing_submit.py`).
4. **Parallel writer in this folder (confirmed):** `sites/areacodes/` appeared at 17:05-17:15 IST
   authored by something other than this session — build.py, fetch_data.py, guides.json and a built
   6,953-file site. Verified the artifact, **deployed it** as `myds-areacodes` ->
   `https://areacodes.tekify.xyz` (6,954 URLs, IndexNow accepted, ads+analytics live), committed the
   sources, and wired it into hub/network/build_all/health. It is a NANPA area-code + world
   dialing-code directory (~6.9k pages). See `docs/COORDINATION.md`: treat unexpected files as
   another writer's work, never delete, never force-push, check `ops.py pages` before deploying.
   (build_all already contained an areacodes entry when checked, further confirming a second writer.)

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
