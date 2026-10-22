# STATE — current status

> Last updated: 2026-10-22 ~23:40 IST (DeepSeek agent, repo `myds`). Round 15 of the goal loop.
> Next session: read this, then `docs/BACKLOG.md`; pick the top ready item. Do not re-plan.

## One-line status

**11 properties live (~113,500 pages) with HilltopAds display ads, Travelpayouts affiliate cards,
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

≈ **113,500 pages** ours. Every property: canonical URLs, JSON-LD, breadcrumbs, sitemaps, robots,
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
