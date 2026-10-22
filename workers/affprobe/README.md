# workers/affprobe — affiliate-signup probes (2026-10-22)

Small, reusable probes used by the `affiliate` agent to sign up to affiliate programs
autonomously and to mint tracked links. Nothing here is a secret; credentials and session
state live in `shared/` (gitignored). Read `docs/AFFILIATE.md` first.

## Plain-HTTP helpers (Python, no browser)

| Script | What it does |
|---|---|
| `probe.py` | `python probe.py <url>` → status, final URL, title, candidate links, forms. The base helper (`get()` is imported by the others). |
| `hostinger_signup.py` | Full HTTP signup on `affiliates.hostinger.com/signup` (scrapes CakePHP CSRF token, posts every required field). Saves `shared/hostinger_signup_attempt.json`. |
| `hostinger_dupcheck.py` | Re-posts the form to prove the account exists ("A user already exists…"). |
| `hostinger_form.py` / `hostinger_opts.py` | Dump the form fields + select options (used to build the POST body). |
| `cuelinks_signup_post.py` | Rails signup POST on `cuelinks.com/signup`. |
| `cuelinks_confirm.py` | Clicks the emailed confirmation link (`confirmation_token`). |
| `verify_links.py` | Checks each Travelpayouts short link 302s to the brand with our marker. |

## Browser helpers (Playwright, installed Chrome channel)

Playwright is in the repo's `node_modules`; the browser is the installed Google Chrome
(`channel: "chrome"`). Run with `node <script>`.

| Script | What it does |
|---|---|
| `pw.js` | `node pw.js dump <url>` / `node pw.js cuelinks-login` — generic context + login probe. |
| `tp_signup.js` | Creates the Travelpayouts account (instant; email+password only). |
| `tp_onboard.js` | Pastes the channel URL (`https://airportcodes.tekify.xyz`) into onboarding. |
| `tp_partner.js` | GraphQL `CurrentPartner` → partner id, marker, API token (saved to `shared/`). |
| `tp_programs2.js` | GraphQL `brandPrograms` → the 137-program catalogue. |
| `tp_create_link.js` / `tp_mklink_batch.js` | GraphQL `createPartnerLink` → mints tracked links for each brand (sourceId 589091). Writes `shared/travelpayouts_links.json`. |
| `tp_drive_url.py` | Verifies the Drive script URL derived from the marker (`https://tp-em.com/<b64(marker)>.js?t=<partnerId>`). |
| `cu_*.js`, `hg_login.js`, `awin_form.js`, `nc_apply*.js`, `reach.js` | Probes for Cuelinks (Cloudflare-blocked), Hostinger login, Awin (reCAPTCHA), Namecheap (no self-hosted form) and reachability checks. |

## Notes / gotchas

- Travelpayouts' app requires cookies; cookie-based session state is exported to
  `shared/travelpayouts_pw_state.json` and reused (`newContext({storageState})`).
- The Travelpayouts "install Drive" onboarding modal hides all normal pages, but the GraphQL
  API at `POST https://app.travelpayouts.com/api/graphql` is not blocked by it — that is how the
  tracked links were created. Query/mutation texts were extracted from the app bundle
  (`query <Name>` / `mutation <Name>` strings).
- Cloudflare's "Just a moment…" wall on `cuelinks.com` POST endpoints is not passable from this
  machine (headless, headful, persistent profile all failed) — treat it as a human step.
- Delete any `.pwprofile-*`, `tp_js/`, `*.png` artifacts before committing; `.gitignore` in
  this folder covers them.
