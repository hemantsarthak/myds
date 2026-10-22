# moneyds — autonomous revenue portfolio

Agent-operated network of free, data-driven websites on **tekify.xyz**, monetized with
display ads, affiliate links and paid data APIs. Goal: **$1,000/month** within 30–90 days.

Humans: you do not need to do anything unless an agent messages you about a payout / KYC /
identity step. To resume work, just say **"continue"**.

- Agents: read `AGENTS.md` first, then `docs/STATE.md` and `docs/BACKLOG.md`.
- Strategy: `docs/STRATEGY.md` · Sites: `docs/SITES.md` · Money: `docs/REVENUE.md`
- Credentials/notes (not in git): `shared/`

## Current properties

| Site | What it is | Status |
|---|---|---|
| https://pincode.tekify.xyz | India pincode / post office lookup (38,936 post offices) | live |

More launching: IFSC bank codes, ZIP codes, RTO codes, SWIFT codes, area codes,
calculators, text tools, and a paid dataset API.

## Stack

Cloudflare Pages (static hosting) · Cloudflare Workers/Functions · R2/D1/KV ·
Python 3.12 build scripts · GitHub Actions/CLI deploy · sitemap + IndexNow.
