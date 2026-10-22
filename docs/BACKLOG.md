# BACKLOG — prioritized, ready to execute

Work top-down. Each item = one session block. Mark done by moving it to the Done section
with the date, and update `docs/STATE.md`.

## P0 — NOW

- [x] P0-1. (2026-10-22) All five sites live on their subdomains with certificates.
- [x] P0-2. (2026-10-22) IndexNow submitted: 15,007 + 10,178 + 8,626 + 17,756 + 4 URLs accepted (200). Bing indexed pages within ~1h.
- [x] P0-3. (2026-10-22) HilltopAds tags live in engine/ads.py; pincode legacy template patched; full rebuild+deploy done.
      rebuild hub/ifsc/airport/zip → redeploy → patch pincode legacy template → verify tags
      render and `ads.txt` served. Record account in `shared/creds.md` + `docs/REVENUE.md`.
- [x] P0-4. (2026-10-22) Committed + pushed; docs updated.

## P1 — more traffic assets (biggest SEO lever)

- [ ] P1-1. `areacodes.tekify.xyz`: US/Canada NANP area codes (+ world country calling codes).
- [x] (2026-10-22) `colleges.tekify.xyz` live: 5,995 US institutions from federal IPEDS (acceptance
      rate, tuition, enrollment, 150% graduation rate) + 3 guides.
- [x] (2026-10-22) `places.tekify.xyz` live: 16k places + 3,144 counties + 51 states (Census data).
- [x] P1-2. (2026-10-22) `calculators.tekify.xyz` live with 53 tools; expand with more niches later.
      salary, BMI, dates) — high-intent US traffic, better ad RPM than data pages.
- [ ] P1-3. `swift.tekify.xyz`: SWIFT/BIC codes by bank/country. Dataset leads (research 2026-10-22):
      https://github.com/lobax/banknames (bank names by BIC from SWIFT registry),
      https://github.com/zapjur/swift-api, https://github.com/abdalrhman-alajlouni/BanksDataWorldWide.
      Check licences before shipping.
- [ ] P1-4. Expand airport site to small airports with ICAO codes (chunked subdomains if needed).
- [ ] P1-5. Expand pincode site: all 23,913 pincodes (shard across subdomain or paginate) — NOTE: pincode project is the other agent's now.
- [x] (2026-10-22) Guide content: 10 hand-written explainers across ifsc/zip/places/airport/calculators
      (`engine/guides.py`, section at /guides/), to lift site quality and capture informational queries.

## P2 — measurement & indexing

- [x] P2-1. (2026-10-22) Self-hosted pageview counter live (`ops.py stats`), injected via engine/analytics.py.
- [ ] P2-2. Weekly IndexNow resubmit script + `lastmod` refresh (cron reminder locally; no server).
- [ ] P2-3. Verify sitemap coverage per site; submit top URLs to search engines manually.
- [ ] P2-4. Check indexing via Bing `site:` queries (no account needed through web_fetch).

## P3 — monetize harder

- [x] P3-1. (2026-10-22) Affiliate: Travelpayouts approved + 15 tracked links live on airport/hub; Hostinger submitted; Cuelinks email-confirmed. Second ad network still needs a human captcha.
- [ ] P3-2. Affiliate layer: commercial-intent pages get contextual product links.
- [ ] P3-3. x402 paid dataset API (`api.tekify.xyz`) — USDC on Base to our wallet.
- [ ] P3-4. AdSense/Ezoic once traffic > 10k visits/mo (needs human Google step).
- [ ] P3-5. Digital product storefront (Gumroad) prepared, payout needs one human step.

## P4 — compounding

- [ ] P4-1. Weekly traffic/revenue report into docs/REVENUE.md; prune losers.
- [ ] P4-2. Backlinks: open dataset pages, free embeddable widgets, directory submissions.
- [ ] P4-3. Consider selling the strongest site(s) at 25–35× monthly revenue.

## Done

- [x] 2026-10-22 — Calculators site live: calculators.tekify.xyz (53 tools, maths verified).

- [x] 2026-10-22 — Repo foundation, agent protocol, strategy, roadmap.
- [x] 2026-10-22 — Ops CLI (deploy/attach/DNS/IndexNow/inbox), engine, build_all.
- [x] 2026-10-22 — Pincode site migrated + redeployed; hub at apex.
- [x] 2026-10-22 — IFSC site (15k pages) live at ifsccodes.tekify.xyz.
- [x] 2026-10-22 — Airport site (10k pages) live at airportcodes.tekify.xyz.
- [x] 2026-10-22 — ZIP site (17.7k pages) built + deployed at zipcodes.tekify.xyz.
- [x] 2026-10-22 — Autonomous email inbox at *@tekify.xyz (Email Routing + Worker + KV).
