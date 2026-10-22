# Portfolio readiness report

_Last updated: 2026-10-24. This is the one-page answer to "what exists, what works, and what is missing
before revenue"._

## What exists

Twelve live properties on **tekify.xyz**, all static, all generated from documented public datasets:

| Property | URL | Pages | Source |
|---|---|---|---|
| Hub | tekify.xyz | 18 (12 data analyses) | — |
| IFSC Codes India | ifsccodes.tekify.xyz | 19,511 | Razorpay IFSC (MIT) |
| US ZIP Codes | zipcodes.tekify.xyz | 17,759 | Census / GeoNames |
| US Places & Counties | places.tekify.xyz | 19,203 | Census |
| US Colleges | colleges.tekify.xyz | 6,056 | NCES / IPEDS |
| US Hospitals | hospitals.tekify.xyz | 5,888 | CMS |
| US Nursing Homes | nursinghomes.tekify.xyz | 15,056 | CMS |
| US Home Health | homehealth.tekify.xyz | 12,777 | CMS |
| US Dialysis Centers | dialysis.tekify.xyz | 7,809 | CMS |
| Area Codes | areacodes.tekify.xyz | 6,954 | NANP / world codes |
| Airport Codes | airportcodes.tekify.xyz | 10,181 | OurAirports |
| Calculators | calculators.tekify.xyz | 75 | — |

**Total: 121,287 URLs.** Every site: HTTPS-enforced (TLS 1.2+), canonical tags, JSON-LD, sitemap,
robots.txt, IndexNow key, `llms.txt`, search, ads and cookie-free analytics. The health check passes on
all twelve and the full audit reports **0 failures / 0 warnings**.

## What is ready for revenue

- **HilltopAds** display ads live on every page (popunder + in-page push + banner). Payout min $20,
  weekly Tuesday, crypto/PayPal available.
- **Travelpayouts** affiliate links on airport pages + hub (approved, 15 tracked links).
- **Cuelinks** (India affiliate) account confirmed.
- Payout wallets recorded in `shared/wallets-payout.json`.

## What is missing — and why

**Search-engine indexing.** Google and Bing currently index **zero** pages of the portfolio. The domain
is new, has no inbound links from established sites, and every autonomous path to create one is blocked:

| Channel | Status |
|---|---|
| Sitemaps + IndexNow (Bing/Yandex/Seznam) | ✅ submitted: 121,287 custom-domain URLs + 70,406 pages.dev URLs + 304 github.io URLs |
| GitHub Pages site (github.io) | ✅ live, 304 URLs, submitted to IndexNow — the crawl target |
| Hugging Face / Zenodo datasets | ⏸ payload ready, needs account (email verification) |
| npm / PyPI packages | ⏸ payload ready, needs account (email verification) |
| Medium articles | ⏸ 3 drafts ready, needs account |
| Google Search Console | ❌ needs the human (1 minute) |
| Bing Webmaster Tools | ❌ needs the human (30-second press-and-hold) |
| Substack publication | ❌ captcha (30 seconds, human) |

## The fastest path to revenue

1. **Google Search Console** (1 min): add the Domain property `tekify.xyz`, paste the
   `google-site-verification=…` token into the chat. The agent adds the DNS record
   (`scripts/verify_domain.py`) and submits the sitemaps + requests indexing. This is the single
   highest-leverage action.
2. **Wait for Bing** (automatic): the IndexNow queues are large and fresh; Bing typically starts
   indexing a new host within 24–72 hours of submission. No action needed.
3. **Publishing push** (agent, after 05:30 IST): Hugging Face + Zenodo datasets, npm + PyPI packages,
   Medium articles — each is an indexable page on a platform search engines already crawl.

## Realistic timeline

- **Days 1–7:** indexing begins (Bing first, Google after GSC or naturally via links). No revenue.
- **Weeks 2–4:** long-tail pages start ranking; first ad impressions; first affiliate clicks.
- **Weeks 4–12:** the calculators and the healthcare directories are the most likely to produce
  meaningful traffic; HilltopAds pays out at $20, Travelpayouts at $50.

The $1,000/month target needs roughly 150k–400k monthly pageviews at typical display-ad RPMs, or a
smaller number with higher-RPM healthcare/finance traffic. The portfolio has the page inventory; the
open variable is indexing speed, which is why the human actions above matter more than any further
content work.
