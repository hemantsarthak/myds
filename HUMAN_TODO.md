# HUMAN TODO — the small actions that unblock revenue

> Updated **2026-10-25 ~00:15 IST** after the 14-round high-CPC content session. The portfolio is
> built, deployed and verified: **13 sites, 123,512 URLs**, HilltopAds **approved** and serving,
> Infolinks applied, Travelpayouts live, analytics live. Revenue is **`$0.00`** because there are
> **zero human visitors** yet — the remaining constraints are search ranking time plus the actions
> below, which need your Google/Microsoft account.

## 1. Google AdSense — HIGHEST VALUE (~10 minutes)

This is the only high-CPC ad network that fits a 120k-page content portfolio. Hilltop/Infolinks pay
a few dollars per 1k views; AdSense pays **$10–40 RPM** on the finance/insurance/health pages we
built this week.

1. Open https://adsense.google.com/start/ and sign in with your Google account.
2. Add site `tekify.xyz` (and, if offered, `healthinsurance.tekify.xyz`). Use the domain-verification
   option (the agent can add the DNS/ads.txt record in seconds if you paste the snippet here).
3. Complete the account details (country, payments profile — this is the part only you can do).
4. Tell the agent when the account exists; it will add the AdSense code to the sites, submit
   `ads.txt`, and monitor approval.

AdSense review can take a few days and may ask for content/policy changes; the agent handles those.

## 2. Google Search Console — HIGH VALUE (~1 minute)

Two `google-site-verification=` TXT records already exist in DNS (one added 2026-10-24), so this may
already be done. If not verified:

1. Open https://search.google.com/search-console → **Add property** → **Domain** → `tekify.xyz`.
2. It shows a TXT value — paste it here (or into `shared/creds.md`) and the agent adds the DNS record.
3. Click **Verify**, then submit `https://tekify.xyz/sitemap.xml` under **Sitemaps** and use
   **URL Inspection → Request indexing** on the hub and a few guides.

Unlocks: sitemap submission, indexing requests, and the impression/ranking data the agent is
currently blind to.

## 3. HilltopAds payout wallet when balance nears $20 (~1 minute, not needed yet)

HilltopAds website approval is now **APPROVED**; the balance is `$0.00` with 0 impressions. When the
agent tells you the balance is approaching **$20**, paste one of the wallets from
`shared/wallets-payout.json` (BTC / USDT-TRC20 / ETH) into HilltopAds → My Account → Payment system.
No KYC is required for crypto payouts.

## 4. (Optional) Bing Webmaster Tools

Microsoft blocked the agent's automated account creation ("unusual activity"). If you sign in to
https://www.bing.com/webmasters with your existing Microsoft account in the agent Chrome window, the
agent takes over (adds site, verifies DNS, submits all URLs). Optional — Bing already receives URLs
via IndexNow.

## 5. (Optional) GitHub token scope for the root host

The fine-grained PAT cannot write to `hemantsarthak/hemantsarthak.github.io`, so the root GitHub
Pages host stays an empty 404. Adding that repo to the token's repository access lets the agent
publish the root landing page + IndexNow key file. Low value; skip unless convenient.

---

**Status and full history:** `docs/STATE.md` (session wrap-up at the top) · `docs/HIGH_CPC.md`
(content plan/progress) · `docs/ADS.md` (monetization) · `docs/REVENUE.md` (ledger).
