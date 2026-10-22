# SITES — registry of deployed properties

Columns: site | Pages project | URL | pages | ads | analytics | status | notes

| site | Pages project | URL | pages | ads | analytics | status |
|---|---|---|---|---|---|---|
| pincode-india | pincode-india | https://pincode.tekify.xyz | 8,620 | none yet | CF Web Analytics TBD | LIVE (inherited, needs ad tags + re-deploy from this repo) |

## Planned (see docs/BACKLOG.md)

ifsc.tekify.xyz · zip.tekify.xyz · rto.tekify.xyz · stdcode.tekify.xyz ·
areacode.tekify.xyz · swift.tekify.xyz · timezone.tekify.xyz · calc.tekify.xyz ·
textools.tekify.xyz · api.tekify.xyz

## Deployment convention

- One Cloudflare Pages project per site: `npx wrangler pages deploy site --project-name=<slug>`
- Attach `<slug>.tekify.xyz` via API (`/accounts/{acct}/pages/projects/{name}/domains`)
- Every site ships: `/sitemap.xml` (+ index if >10k), `/robots.txt`, `/<indexnow-key>.txt`,
  `/404.html`, JSON-LD, CF Web Analytics beacon, ad slots.
- Build output never committed: `.gitignore` has `site/`.

## Ownership / accounts

- Cloudflare account `c01fe438c7960466670d312e55164037` (Monetec2@gmail.com) — shared with
  other agents; only touch our own Pages projects/zones entries.
- GitHub `hemantsarthak/myds` (public).
- Ads: TBD in `shared/creds.md`.
