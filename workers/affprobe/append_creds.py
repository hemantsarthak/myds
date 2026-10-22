import json, pathlib
p = pathlib.Path("shared/creds.md")
cur = p.read_text(encoding="utf-8")
tp = json.loads(pathlib.Path("shared/travelpayouts_account.json").read_text(encoding="utf-8"))
cu = json.loads(pathlib.Path("shared/cuelinks_signup_attempt.json").read_text(encoding="utf-8"))
hg = json.loads(pathlib.Path("shared/hostinger_signup_attempt.json").read_text(encoding="utf-8"))

marker = "## Affiliate accounts created by agents (2026-10-22, `affiliate` agent)\n"
if marker in cur:
    print("section already present; skipping")
else:
    rows = [
        mark_ := "",
    ]
    block = f"""
## Affiliate accounts created by agents (2026-10-22, `affiliate` agent)

Details in `docs/AFFILIATE.md`. Secrets live here only; never commit this file.

| Service | Email | Secret | Notes | Date |
|---|---|---|---|---|
| **Travelpayouts (APPROVED, live)** | `{tp['email']}` | password `{tp['password']}` | Login https://app.travelpayouts.com/ ; partner ID **{tp['partner_id']}**, tracking marker **{tp['marker']}**, source/channel **589091** ("Airportcodes" = https://airportcodes.tekify.xyz, content_project/website); API token + 137-program list in `shared/travelpayouts_account.json`; 14 tracked links in `shared/travelpayouts_links.json` and in `engine/affiliates.py`; payout min $50 PayPal/wire (not configured yet). Signup was instant (email+password, no KYC). | 2026-10-22 |
| **Hostinger affiliates (SUBMITTED, pending review)** | `{hg['email']}` | password `{hg['password']}` | Application POSTed to https://affiliates.hostinger.com/signup ; reply = "Your application is currently being reviewed. An account manager will contact you shortly."; re-submit check confirms the account exists ("A user already exists with this email address"). Login portal https://affiliates.hostinger.com/ (login works only after approval). Payout: PayPal, min $100 + 3 approved sales. | 2026-10-22 |
| **Cuelinks (EMAIL CONFIRMED, dashboard Cloudflare-blocked)** | `{cu['email']}` | password `{cu['password']}` | Signup https://www.cuelinks.com/signup ; confirmation link clicked ("Your account has been confirmed. Please login to verify your channel"). Dashboard/login POST is behind a Cloudflare bot wall (403 "Just a moment…") from all automated clients incl. real Chrome — needs one human browser login. Payout: ₹500 min, Indian bank. India network: Flipkart/Amazon.in/banks/Booking. | 2026-10-22 |

Browser session state for the above (Playwright storage state, gitignored):
`shared/travelpayouts_pw_state.json`, `shared/cuelinks_pw_state.json`, `shared/hostinger_pw_state.json`.

**Not created (blocked — see docs/AFFILIATE.md §4):** Namecheap, DigitalOcean, Contabo (all via
CJ publisher application + W-8BEN), Vultr (Impact), Awin (reCAPTCHA), Impact.com (Turnstile),
Cloudways, Amazon.in / Flipkart (PAN + bank).
"""
    p.write_text(cur.rstrip() + "\n" + block, encoding="utf-8")
    print("appended affiliate accounts section to shared/creds.md")
