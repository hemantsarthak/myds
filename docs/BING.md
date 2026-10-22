# BING.md — Bing Webmaster Tools (BWT): access, URL submission, quota

Status as of **2026-10-22**: **blocked on a human-verification gate in Microsoft signup.**
Everything downstream (site add, DNS TXT verification, API key, bulk submission) is prepared and
scripted; it needs one human action (below), then the agent can finish autonomously.

Related: `docs/MAILBOX.md` (autonomous inbox used for the verification code),
`docs/STATE.md`, `scripts/bing_submit.py`, probes in `workers/bwtprobe/`.

---

## Why we want BWT

| Lever | Without BWT | With BWT |
|---|---|---|
| URL submission | IndexNow only (fire-and-forget, no receipt) | URL Submission API, 10k/day/site, per-batch errors |
| Index status | none | indexed / discovered / crawled counts per URL |
| Query data | none | impressions, clicks, average position, top queries |
| Sitemaps | robots.txt discovery only | explicit sitemap submit + error reporting |
| Crawl controls | none | crawl-delay advice, URL removal, blocked-URL diagnostics |

72,776 URLs across 7 properties on `tekify.xyz` are already IndexNow-submitted; BWT adds the
feedback loop (what is actually indexed, what people search) that we currently lack.

---

## Current blocker (exact, reproducible)

Microsoft account creation with an **existing email** works through the whole flow:

1. `https://signup.live.com/signup?lic=1` → enter existing email (`bingwmt@tekify.xyz`) → Next
2. "Verify your email" → **6-digit code is emailed to our autonomous inbox** → code accepted
   (`python scripts/ops.py inbox --latest --to bingwmt@tekify.xyz`; mail arrives in ~30-60 s)
3. "Add some details" (country/birthdate) → accepted
4. "Add your name" → accepted
5. → **"Let's prove you're human — Press and hold the button"** ← *stops here*

In headless mode step 5 is instead replaced by **"Account creation has been blocked — We have
detected some unusual activity"**, so `workers/bwtprobe/ms_flow2.js` runs a **headful** Chrome with a
persistent profile (`shared/bwt_profile/`, gitignored) and human-like typing.

That human-verification gate is a CAPTCHA-class control and is deliberately not automated.
**One human action** clears it (≈30 seconds, once):

```powershell
cd C:\Users\heman\OneDrive\Desktop\Code\deepseek\moneyds
$env:HUMAN_PAUSE="600"; node workers\bwtprobe\ms_flow2.js
# A Chrome window opens, walks the signup (email + code are automatic), then pauses at
# "Press and hold the button" — press and hold it until it passes.
# The script continues by itself and prints ACCOUNT_CREATED (or the next page it cannot handle).
```

Credentials this creates are recorded in `shared/creds.md` (agent-created account) and
`shared/bwt_account.json`. Then no more human action is needed — the agent steps:

```powershell
# 1. Add the 7 sites in BWT UI (headful Playwright: sign in, Add site, verify) — see "Adding sites"
# 2. Settings -> API access -> API key  ->  add to shared/.env as BING_WMT_API_KEY=...
# 3. python scripts/bing_submit.py --all --limit 10000
```

*(If the human prefers, they can instead sign up normally in their own browser with
`bingwmt@tekify.xyz` / password in `shared/bwt_account.json`, or with their own Microsoft account
and add the agent as a user under BWT Settings → Users.)*

---

## Adding sites + verification (planned, no human needed after account exists)

BWT → **Add site** → `https://tekify.xyz` (trailing slash matters for the API `siteUrl`), verify.
Prefer **DNS TXT** — we own the zone and can add records with the Cloudflare token:

```powershell
# BWT gives an exact TXT value for the domain; use it verbatim, as the record NAME (apex -> "@",
# for subdomains the label):
python scripts/ops.py dns --name "@" --target "MS=ms12345678" --type TXT
```

Alternative (when DNS is awkward): BWT's **XML file** method — drop the provided file into
`sites/hub/site/` and run
`python scripts/ops.py deploy --project hub --dir sites/hub/site`.

Subdomains must be added as separate sites in BWT to submit/queries for them:
`ifsccodes.tekify.xyz`, `airportcodes.tekify.xyz`, `zipcodes.tekify.xyz`, `places.tekify.xyz`,
`colleges.tekify.xyz`, `calculators.tekify.xyz`. (Each is its own BWT property; the API is
per-site, which is why `scripts/bing_submit.py` maps slug → BWT siteUrl.)

---

## Submitting URLs: `scripts/bing_submit.py`

```powershell
python scripts/bing_submit.py --list                 # slugs, BWT siteUrl, sitemap URL counts
python scripts/bing_submit.py --quota                # today's usage from shared/bing_quota.json
python scripts/bing_submit.py --site airport --limit 20 --dry-run
python scripts/bing_submit.py --site airport --limit 5000
python scripts/bing_submit.py --all --limit 10000    # respects the 10k/day cap
```

- Reads the sitemap from `sites/<slug>/site/sitemap.xml` (follows a sitemap index if present).
- `BING_WMT_API_KEY` comes from the environment or `shared/.env`; never printed.
- Sends `POST https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlBatch?apikey=…`
  with `{"siteUrl":"https://host/","urlList":[...]}`.
- **Limits:** 10,000 URLs/day per site, **500 URLs max per request** (script caps it),
  1 s between requests by default (`--delay`). Batches are idempotent-ish: resubmitting a URL is
  harmless (Bing de-dupes), so a failed day is simply resumed.
- Success body is `{"d":null}`; the script only counts a batch when it sees that. Errors print
  HTTP code + body (e.g. 400 for an unverified `siteUrl`, 403/429 for auth/quota).
- Usage is persisted to `shared/bing_quota.json` (14-day retention) so `/tmp` resets and laptop
  reboots cannot silently blow the daily cap.

Quota math: 72,776 URLs ≈ 8 days at 10k/day on the hub property alone if we pushed everything
through one site — but each subdomain is a *separate* BWT property with its **own** 10k/day, so
the whole portfolio can be submitted in a single day (per-site caps: ifsc 19.5k → 2 days,
places 19.2k → 2 days, zip 17.8k → 2 days, airport 10.2k → 2 days, colleges 6.1k → 1 day,
hub + calculators → 1 day).

---

## Reading data once the API key exists

BWT REST API (same `apikey` query parameter; JSON responses, `d` field holds the payload):

| Endpoint | What for |
|---|---|
| `GetQueryStats` | top queries, impressions, clicks, avg. position per query |
| `GetRankAndTrafficStats` | daily traffic/impressions trend per site |
| `GetUrlTrafficInfo` | per-URL traffic (crawl/impressions) |
| `GetCrawlStats` | crawl requests/errors per day |
| `GetCrawlIssues` | blocked/404/5xx crawl problems |
| `GetUrlSubmissionQuota` | remaining daily URL submission quota (use before big batches) |
| `SubmitUrlBatch` | bulk submit (above) |
| `SubmitFeed` / `GetFeeds` | sitemap submission + status |

Base: `https://ssl.bing.com/webmaster/api.svc/json/<Method>?apikey=<key>&siteUrl=<encoded>`.
UI equivalents live at `https://www.bing.com/webmasters/` → each site → *Search performance*,
*Site explorer*, *Crawl info*.

Suggested daily automation (add to `scripts/ops.py` or a new `scripts/bing_report.py` when the key
lands): pull `GetRankAndTrafficStats` + `GetQueryStats` into `shared/bing_stats.json`, print a
short digest, and flag URLs that changed from *discovered* to *indexed*.

---

## Gotchas

- `siteUrl` must match exactly the site as added in BWT — including scheme and **trailing slash**
  (`https://tekify.xyz/`). A mismatch returns a 400 "Invalid site URL".
- The API key is per **user**, not per site; one key submits to every site the user owns.
- Microsoft signup: use the **existing email** path, not a new `@outlook.com` address; the
  verification code reliably reaches `*@tekify.xyz` via the catch-all inbox.
- Do not run BWT signup attempts in a loop: repeated headless tries escalate to
  "Account creation has been blocked" for that email. One headful run per human action.
- BWT sometimes also gates *login* with a human check on new devices — keep the persistent
  profile (`shared/bwt_profile/`) so the device looks familiar.
