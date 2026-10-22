# BACKLOG — prioritized, ready to execute

Work top-down. Each item = one session block. Mark done by moving it to the Done section
with the date, and update `docs/STATE.md`.

## P0 — foundation (do first)

- [ ] B1. Commit repo foundation (AGENTS.md/docs) and push to `hemantsarthak/myds`.
- [ ] B2. `scripts/cf.py` + `scripts/deploy.py`: Cloudflare API client (zones, dns, pages
      deploy via wrangler, custom-domain attach/verify) + `scripts/indexnow.py`.
- [ ] B3. Migrate `pincode-india` from `_ref_myhermesds/` into `sites/pincode-india/`,
      rebuild, redeploy to project `pincode-india`; confirm pincode.tekify.xyz green.
- [ ] B4. Create crypto payout wallet (USDT-TRC20 primary, BTC + ETH optional) in
      `shared/wallets/`; record address in `shared/creds.md`.
- [ ] B5. Cloudflare Web Analytics enabled on every site (RUM site + beacon injection).
- [ ] B6. IndexNow key file + submit all pincode URLs (batched) to api.indexnow.org.

## P1 — first new revenue asset

- [ ] B7. `engine/sitegen.py`: shared static-site generator (layout, JSON-LD, sitemaps,
      robots, ad slots, analytics, breadcrumbs, internal related links, validator).
- [ ] B8. Sign up for ad network (Monetag first, Adsterra backup) without human help.
      Steps: provision @tekify.xyz mailbox (Email Routing + Worker, or fallback disposable),
      submit tekify.xyz + subdomains, place verification tag, paste tags into engine ads.
- [ ] B9. `ifsc.tekify.xyz`: IFSC dataset site (5k–20k branch pages) + deploy + IndexNow.
- [ ] B10. `zip.tekify.xyz`: US ZIP dataset site (10k pages) + deploy + IndexNow.

## P2 — scale content

- [ ] B11. `rto.tekify.xyz` (vehicle RTO codes) + `stdcode.tekify.xyz` (STD codes).
- [ ] B12. `areacode.tekify.xyz` (world dialing codes + NANP area codes).
- [ ] B13. `swift.tekify.xyz` (SWIFT/BIC by bank) — highest page count.
- [ ] B14. `calc.tekify.xyz`: 50–100 client-side calculators, US/IN finance first.
- [ ] B15. tekify.xyz hub page: brand, links to all sites, About/Privacy/Contact (E-E-A-T).
- [ ] B16. Sitemap index + robots.txt for all sites; internal cross-linking rules.

## P3 — monetize harder

- [ ] B17. Affiliate accounts (instant ones first) + inject links into high-intent pages.
- [ ] B18. x402 paid API (`api.tekify.xyz`) for datasets; USDC on Base to our wallet.
- [ ] B19. AdSense application (needs human Google account) — only after 10k+ visits/mo.
- [ ] B20. Ezoic application at 10k visits/mo; upgrade ad layout.

## P4 — compounding

- [ ] B21. Weekly traffic/revenue report into docs/REVENUE.md; prune losers.
- [ ] B22. Backlink program: open datasets, free widgets/embeds, directory submissions.
- [ ] B23. Digital products (dataset packs) on Gumroad/Payhip once payout human step done.
- [ ] B24. Consider selling the strongest site(s) for 25–35× monthly revenue.

## Done

- (nothing yet)
