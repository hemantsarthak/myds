# HUMAN TODO — 3 small actions that unblock revenue

The portfolio is built and running (12 sites, 121,000+ pages, all live and audited). The one thing
that cannot be done by an agent is proving ownership of the domain to the search engines. Each item
below takes about a minute and unlocks a large amount of automation.

## 1. Google Search Console — HIGHEST VALUE (~1 minute)

1. Open https://search.google.com/search-console (sign in with your Google account).
2. Click **Add property** -> choose **Domain** -> type `tekify.xyz` -> **Continue**.
3. It shows a TXT record value like `google-site-verification=AbC123...`.
4. **Paste that string into the chat** (or into `shared/creds.md`).
   The agent adds the DNS record automatically (`python scripts/verify_domain.py --google "..."`).
5. Click **Verify** in Search Console.

Unlocks: sitemap submission, URL inspection, indexing requests for the hub/insights/calculators, and
search-performance data. This is the single biggest lever for traffic and therefore revenue.

## 2. Bing Webmaster Tools (~30 seconds, one physical step)

1. Double-click `shared\AI Agent - Chrome.lnk` (opens the agent's Chrome window).
2. Go to https://www.bing.com/webmasters and sign up with `bingwmt@tekify.xyz`
   (password is in `shared/creds.md`).
3. The final step is a "press and hold" human check — hold it for ~30 seconds.
4. Tell the agent it is done; it imports the site, verifies DNS and submits all 121,000 URLs.

> 2026-10-24 update: the agent can now read the Microsoft verification code by itself — the
> mailbox `/inbox/latest` endpoint was changed to a `last:` KV pointer so it works even when the
> free-tier KV `list()` quota is exhausted. So the agent can drive the signup; the only genuinely
> human step is the press-and-hold challenge. If you already have a Microsoft account (you use
> OneDrive), **signing in** instead of signing up is fastest.

## 3. Substack — publication created, then SUSPENDED (2026-10-23)

`tekifydata.substack.com` was created but Substack suspended it for a Spam & Phishing policy
violation (0 posts were published). Not revenue-critical; use the Appeals Center only if you
want that channel. The agent is focusing on search indexing instead.

## 4. (Optional, 1 minute) GitHub token scope for the root host

The agent created the repo `hemantsarthak/hemantsarthak.github.io` but the fine-grained GitHub token
cannot write to it (403). If you add that repo to the token's *Repository access* (or set access to
"All repositories"), the agent can publish a root landing page and host the IndexNow key file at the
host root — which unlocks IndexNow submission for the whole `hemantsarthak.github.io` host.

---

Everything else runs itself: daily GitHub Actions health check (08:47 IST), IndexNow submissions,
ads and analytics on every page, and the agent continues building content each session.

Status and full history: `docs/STATE.md`. Revenue ledger: `docs/REVENUE.md`.
