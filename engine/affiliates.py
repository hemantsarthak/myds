#!/usr/bin/env python3
"""engine/affiliates.py — affiliate-program registry and link builder.

PURE DATA + tiny helpers. No secrets here (public tracking markers only; API tokens and
passwords live in `shared/` which is gitignored). Read `docs/AFFILIATE.md` for the full
application state of every program, the exact blockers, and what a human still has to do.

How the Lead should use it:

    from engine.affiliates import links_for, drive_snippet
    links_for("airports")          # -> [(label, href, rel, note), ...]  only TRACKED links
    links_for("calculators")       # -> same, for a different site
    links_for("zip", kind="hosting")   # narrow by placement kind
    drive_snippet()                # -> "<script async src=...>" or "" if disabled

Conventions
-----------
* `status` per program: "approved" (account usable now), "pending" (submitted, awaiting
  review), "blocked" (cannot be completed autonomously — see blocker), "todo" (not started).
* A link is only returned by `links_for()` when the program is approved AND the link is
  `tracked` (it carries our id, so clicks convert). Untracked placeholder links are never
  emitted into pages.
* `rel` is always "sponsored nofollow noopener" for currently monetised links; the renderer
  in `engine/affiliate.py` adds the disclosure line that affiliate links legally require.

Everything below was verified 2026-10-22 by the `affiliate` agent (see docs/AFFILIATE.md).
"""
from __future__ import annotations

from urllib.parse import quote, urlencode

# --------------------------------------------------------------------------- sites
# site slug -> (display name, which placement kinds make sense there)
SITES: dict[str, dict] = {
    "hub": {"name": "tekify.xyz", "kinds": ["hosting", "domains", "vps", "vpn", "travel"]},
    "ifsc": {"name": "IFSC Codes India", "kinds": ["hosting", "domains", "vpn"]},
    "airports": {"name": "Airport Codes", "kinds": ["travel", "flights", "hotels", "esim",
                                                    "flight_compensation", "car_rental",
                                                    "tours", "vpn"]},
    "zip": {"name": "US ZIP Codes", "kinds": ["hosting", "domains", "vpn", "movers", "insurance"]},
    "calculators": {"name": "Calculators", "kinds": ["finance", "vpn", "hosting"]},
}

# --------------------------------------------------------------------------- travelpayouts
# One approved account (instant signup, no KYC, USD) that is the network for 137 travel
# brands. Our public tracking marker is in every link; the Drive script auto-places offers.
TP = {
    "id": "travelpayouts",
    "name": "Travelpayouts (network: Booking.com, Aviasales, Kiwi, Klook, AirHelp, eSIM…)",
    "login": "https://app.travelpayouts.com/",
    "apply_url": "https://www.travelpayouts.com/",
    "status": "approved",
    "account_id": "764877",
    "marker": "793747",
    "currency": "USD",
    "payout": "min $50; PayPal / wire / Payoneer (payment details not filled yet)",
    "cookie_days": 30,
    "commission": "varies by brand: Booking.com ~4% of stay value, Aviasales/Kiwi 1.1–1.6% of "
                  "ticket, Klook 2–5%, eSIM 10–20%, AirHelp ~€10–30 per compensation claim",
    "sites": ["airports", "hub", "zip"],
    "kinds": ["travel", "flights", "hotels", "esim", "flight_compensation", "car_rental",
              "tours", "vpn"],
    "restrictions": "No coupon/deal sites for some brands; no incentivised clicks; traffic must "
                    "be your own content. Airport/travel content is explicitly welcome.",
    "notes": "Signup is email+password and lands straight in the partner dashboard (no email "
             "confirmation). The only gated UI is a mandatory 'install Drive' onboarding modal; "
             "the link generator opens after choosing an install option. The Drive script URL "
             "itself is derivable and verified working (see drive_snippet()).",
    "human_action": "None to earn: Drive script on a live site is enough. To withdraw: add payout "
                    "details (PayPal/wire) in the dashboard once balance > $50.",
}

# brand id -> (label, dest, why it fits our pages). Ids verified through the partner API.
TP_BRANDS: dict[str, dict] = {
    "10": {"label": "Economybookings \u2014 airport car hire",
            "kinds": ["car_rental"], "note": "per booking",
            "short": "https://economybookings.tpo.mx/6u9JkTnk", "full": "https://tp.media/r?campaign_id=10&marker=793747&p=2018&trs=589091&u=https%3A%2F%2Fwww.economybookings.com%2F"},
    "86": {"label": "Compensair \u2014 flight compensation",
            "kinds": ["flight_compensation"], "note": "fee per successful claim",
            "short": "https://compensair.tpo.mx/5Mg9Cii4", "full": "https://tp.media/r?campaign_id=86&marker=793747&p=4129&trs=589091&u=https%3A%2F%2Fcompensair.com%2F"},
    "89": {"label": "Tiqets \u2014 attraction tickets",
            "kinds": ["tours"], "note": "~4% of booking",
            "short": "https://tiqets.tpo.mx/SFw2dOpD", "full": "https://tp.media/r?campaign_id=89&marker=793747&p=2074&trs=589091&u=https%3A%2F%2Fwww.tiqets.com%2F"},
    "100": {"label": "Aviasales \u2014 compare flight prices",
            "kinds": ["flights", "travel"], "note": "1.1\u20131.6% of ticket",
            "short": "https://aviasales.tpo.mx/J2vylIw9", "full": "https://tp.media/r?campaign_id=100&marker=793747&p=4114&trs=589091&u=https%3A%2F%2Faviasales.com%2F"},
    "111": {"label": "Kiwi.com \u2014 cheap flights",
            "kinds": ["flights", "travel"], "note": "~1.3% of ticket",
            "short": "https://kiwi.tpo.mx/i2nhb9Sp", "full": "https://tp.media/r?campaign_id=111&marker=793747&p=4136&trs=589091&u=https%3A%2F%2Fwww.kiwi.com%2F"},
    "120": {"label": "AirHelp \u2014 claim flight-delay compensation",
            "kinds": ["flight_compensation"], "note": "fee per successful claim",
            "short": "https://airhelp.tpo.mx/U4U92Tbc", "full": "https://tp.media/r?campaign_id=120&marker=793747&p=9139&trs=589091&u=https%3A%2F%2Fairhelp.com%2F"},
    "137": {"label": "Klook \u2014 airport transfers & attractions",
            "kinds": ["tours", "travel"], "note": "2\u20135% of booking",
            "short": "https://klook.tpo.mx/pbnLEpzr", "full": "https://tp.media/r?campaign_id=137&marker=793747&p=4110&trs=589091&u=https%3A%2F%2Fwww.klook.com%2F"},
    "147": {"label": "GetTransfer \u2014 airport transfer quotes",
            "kinds": ["travel", "car_rental"], "note": "per booking",
            "short": "https://gettransfer.tpo.mx/XkfzKQvS", "full": "https://tp.media/r?campaign_id=147&marker=793747&p=4439&trs=589091&u=https%3A%2F%2Fwww.gettransfer.com%2F"},
    "172": {"label": "QEEQ \u2014 car rental comparison",
            "kinds": ["car_rental"], "note": "per booking",
            "short": "https://qeeq.tpo.mx/dl5eOAOs", "full": "https://tp.media/r?campaign_id=172&marker=793747&p=4845&trs=589091&u=https%3A%2F%2Fwww.qeeq.com%2F"},
    "209": {"label": "Radical Storage \u2014 luggage storage",
            "kinds": ["travel"], "note": "per booking",
            "short": "https://radicalstorage.tpo.mx/7fFq6x3N", "full": "https://tp.media/r?campaign_id=209&marker=793747&p=5867&trs=589091&u=https%3A%2F%2Fradicalstorage.com%2F"},
    "224": {"label": "Yesim \u2014 unlimited travel data",
            "kinds": ["esim"], "note": "per plan",
            "short": "https://yesim.tpo.mx/XOKYFkQD", "full": "https://tp.media/r?campaign_id=224&marker=793747&p=5998&trs=589091&u=https%3A%2F%2Fyesim.tech%2F"},
    "541": {"label": "Airalo \u2014 travel eSIM data",
            "kinds": ["esim"], "note": "10\u201320% of plan",
            "short": "https://airalo.tpo.mx/EzBTKOZi", "full": "https://tp.media/r?campaign_id=541&marker=793747&p=8310&trs=589091&u=https%3A%2F%2Fwww.airalo.com%2F"},
    "627": {"label": "Welcome Pickups \u2014 airport transfers",
            "kinds": ["travel", "tours"], "note": "per booking",
            "short": "https://tpo.mx/45XoGj4Y", "full": "https://tp.media/r?campaign_id=627&marker=793747&p=8919&trs=589091&u=https%3A%2F%2Fwww.welcomepickups.com%2F"},
    "629": {"label": "Saily \u2014 travel eSIM",
            "kinds": ["esim"], "note": "up to 20% of plan",
            "short": "https://saily.tpo.mx/volLXceq", "full": "https://tp.media/r?campaign_id=629&marker=793747&p=8979&trs=589091&u=https%3A%2F%2Fsaily.com%2F"},
    "633": {"label": "KKday \u2014 tours and transfers",
            "kinds": ["tours"], "note": "~3% of booking",
            "short": "https://kkday.tpo.mx/XK7ySd6P", "full": "https://tp.media/r?campaign_id=633&marker=793747&p=9074&trs=589091&u=https%3A%2F%2Fwww.kkday.com%2F"},
}

# --------------------------------------------------------------------------- other programs
PROGRAMS: dict[str, dict] = {
    "hostinger": {
        "name": "Hostinger affiliates",
        "apply_url": "https://www.hostinger.com/affiliates",
        "login": "https://affiliates.hostinger.com/",
        "status": "pending",
        "applied_email": "hostinger@tekify.xyz",
        "commission": "up to 60% of first purchase (tiered)",
        "payout": "PayPal, min $100 and a 3-sale approval minimum",
        "cookie_days": 30,
        "sites": ["hub", "zip", "ifsc", "calculators"],
        "kinds": ["hosting", "vps", "domains"],
        "link_template": "https://www.hostinger.com/?REFERRALCODE={code}",
        "restrictions": "No PPC/impression-based advertising of their brand; no coupon sites.",
        "notes": "Application submitted 2026-10-22 (PostAffiliatePro-style /signup form, all "
                 "fields HTTP). Server replied 'A user already exists with this email address' "
                 "on a re-run, so the account exists; login returns the login form because "
                 "applications are manually reviewed ('Your application is currently being "
                 "reviewed. An account manager will contact you shortly.').",
        "human_action": "Wait for review (no human step). After approval, copy the referral code "
                        "from the dashboard and put it in AFFILIATE_CODES below.",
    },
    "cuelinks": {
        "name": "Cuelinks (India network: 1000+ merchants incl. Flipkart/Amazon India/Booking)",
        "apply_url": "https://www.cuelinks.com/signup",
        "login": "https://www.cuelinks.com/login",
        "status": "pending",
        "applied_email": "cuelinks@tekify.xyz",
        "commission": "per merchant (typically 1–10% of order; fashion/travel higher)",
        "payout": "min ₹500 to an Indian bank account (₹20,000 for non-Indian banks)",
        "cookie_days": 30,
        "sites": ["hub", "calculators", "zip", "ifsc"],
        "kinds": ["finance", "hosting", "travel"],
        "notes": "Email confirmed 2026-10-22 (confirmation link clicked; 'Your account has been "
                 "confirmed. Please login to verify your channel'). The publisher dashboard sits "
                 "behind a Cloudflare bot wall that rejects every automated client (HTTP 403 / "
                 "'Just a moment…', including headless + headful real Chrome), so channel "
                 "verification and campaign links could not be completed autonomously.",
        "human_action": "Log in once in a normal browser, verify the channel "
                        "(https://tekify.xyz or a subdomain), then paste the per-merchant links.",
    },
    "namecheap": {
        "name": "Namecheap affiliate",
        "apply_url": "https://www.namecheap.com/affiliates/",
        "status": "blocked",
        "commission": "varies by platform (Impact / CJ)",
        "payout": "via network (PayPal or bank)",
        "cookie_days": 30,
        "sites": ["hub", "zip", "ifsc"],
        "kinds": ["domains", "hosting", "vpn"],
        "notes": "Namecheap does not self-host the programme: its 'Apply now' CTA points at "
                 "third-party networks (Impact / CJ). Plain HTTP to namecheap.com/affiliates is "
                 "HTTP 403 Cloudflare; a real Chrome session gets the marketing page, and the "
                 "application itself happens inside the network portal.",
        "human_action": "Apply through Impact or CJ once we have traffic history (networks reject "
                        "zero-traffic publishers), or accept a manual review delay.",
    },
    "digitalocean": {
        "name": "DigitalOcean affiliate (10% recurring for 12 months)",
        "apply_url": "https://www.digitalocean.com/affiliates",
        "status": "blocked",
        "commission": "10% of the referred customer's monthly spend for 12 months",
        "payout": "via CJ (Commission Junction): bank/PayPal, W-8BEN tax form for non-US",
        "cookie_days": 30,
        "sites": ["hub", "calculators", "zip"],
        "kinds": ["vps", "hosting"],
        "notes": "Their own referral programme pays in DigitalOcean credit (not cash). The cash "
                 "affiliate programme runs entirely on CJ: 'Simply sign up with the link below to "
                 "join the program via the CJ (Commission Junction) affiliate network.'",
        "human_action": "CJ publisher application + W-8BEN tax form + payout details (identity/tax "
                        "step a bot cannot complete).",
    },
    "contabo": {
        "name": "Contabo affiliate (VPS / dedicated)",
        "apply_url": "https://contabo.com/en/affiliate-program/",
        "status": "blocked",
        "commission": "per sale, tiered",
        "payout": "via CJ",
        "cookie_days": 30,
        "sites": ["hub", "calculators"],
        "kinds": ["vps"],
        "notes": "The affiliate page's primary CTA is signup.cj.com publisher signup "
                 "(cid=4639721) — i.e. same CJ gated application as DigitalOcean.",
        "human_action": "Same CJ application/tax step as DigitalOcean (do both at once).",
    },
    "vultr": {
        "name": "Vultr affiliate",
        "apply_url": "https://www.vultr.com/affiliate/",
        "status": "blocked",
        "sites": ["hub", "calculators"],
        "kinds": ["vps"],
        "notes": "/affiliate/ returns HTTP 403 Cloudflare to plain HTTP; a real browser redirects "
                 "to brand assets. Programme is run through Impact.",
        "human_action": "Impact publisher application (gated network).",
    },
    "cloudways": {
        "name": "Cloudways affiliate (up to $125/sale)",
        "apply_url": "https://www.cloudways.com/en/web-hosting-affiliate-program.php",
        "status": "todo",
        "commission": "up to $125 per sale",
        "sites": ["hub", "calculators"],
        "kinds": ["hosting"],
        "notes": "Signup is a JS app at unified.cloudways.com/signup (renders no form over plain "
                 "HTTP). Was not attempted in depth because the programme pays via their own "
                 "publisher portal and needs a paying customer to seed the account.",
        "human_action": "None yet; retry with the browser probe if hosting placements convert.",
    },
    "amazon_in": {
        "name": "Amazon Associates India",
        "apply_url": "https://affiliate-program.amazon.in/signup",
        "status": "todo",
        "commission": "0.2–9% by category",
        "payout": "Indian bank account + PAN; min ₹2,500 (bank) / ₹1,000 (gift card)",
        "cookie_days": 1,
        "sites": ["calculators", "zip"],
        "kinds": ["books", "finance"],
        "notes": "Programme page is reachable over HTTP (200) but the application requires a "
                 "verified Amazon.in account plus PAN and bank details, and 3 qualifying sales in "
                 "180 days. Payout identity data is a human step.",
        "human_action": "PAN + bank account (tax/identity) at payout setup time.",
    },
    "flipkart": {
        "name": "Flipkart Affiliate",
        "apply_url": "https://affiliate.flipkart.com/",
        "status": "todo",
        "commission": "up to 10% by category",
        "payout": "Indian bank account; PAN required",
        "cookie_days": 1,
        "sites": ["calculators"],
        "kinds": ["books", "finance"],
        "notes": "Portal is an Angular SPA (only a login form in the HTML) and pays to an Indian "
                 "bank account tied to tax identity.",
        "human_action": "PAN + bank account.",
    },
    "awin": {
        "name": "Awin (network: Booking.com, Skyscanner, many travel brands)",
        "apply_url": "https://ui.awin.com/publisher-signup/en/awin/step1",
        "status": "blocked",
        "commission": "per advertiser",
        "payout": "min $20 via bank/PayPal",
        "cookie_days": 30,
        "sites": ["airports", "hub"],
        "kinds": ["travel", "flights", "hosting"],
        "notes": "Signup form includes a Google reCAPTCHA field (g-recaptcha-response) — cannot be "
                 "solved over HTTP. Their security/QA also rejects new sites without traffic.",
        "human_action": "One human reCAPTCHA solve at the step1 URL with awin@tekify.xyz.",
    },
    "impact": {
        "name": "Impact.com (network: Namecheap, Vultr, many SaaS)",
        "apply_url": "https://app.impact.com/secure/registration/basicInfo.ihtml",
        "status": "blocked",
        "sites": ["hub"],
        "kinds": ["hosting", "vpn", "domains"],
        "notes": "Registration endpoint returns HTTP 403 Cloudflare managed challenge "
                 "(Turnstile) to every HTTP client, including a real Chrome session.",
        "human_action": "One human Turnstile pass at the registration URL with impact@tekify.xyz.",
    },
}

# The approved network account is also a normal program entry (so status queries see it).
PROGRAMS["travelpayouts"] = TP
# Travelpayouts earns through a script as well as through links; keep that visible to callers.
PROGRAMS["travelpayouts"]["script"] = True

# Referral codes learned from provider dashboards (filled in after approval — never secrets).
AFFILIATE_CODES: dict[str, str] = {
    # "hostinger": "",   # paste REFERRALCODE after approval
}

# Set True by the Lead once the wire-in is deployed (lets links_for() be used for tests).
MONETIZATION_ON = True


# --------------------------------------------------------------------------- helpers
def _tp_click(brand_id: str, promo: str = "", dest: str = "") -> str:
    """Build a Travelpayouts click link. Needs an actual promo id and an active program
    subscription on the marker; `links_for` only emits these when both are known."""
    params = {
        "shmarker": TP["marker"],
        "promo_id": promo,
        "source_type": "link",
        "type": "click",
        "campaign_id": brand_id,
    }
    base = "https://tp.media/click?" + urlencode(params)
    if dest:
        base += "&u=" + quote(dest, safe="")
    return base


def drive_snippet() -> str:
    """Travelpayouts Drive auto-affiliate script for our account (verified HTTP 200, returns
    real JS). Drive finds commercial anchors on a page and rewrites them into tracked links,
    so it monetises pages without hand-placed affiliate URLs. Empty string when disabled."""
    if not MONETIZATION_ON:
        return ""
    return ('<script async src="https://tp-em.com/NzkzNzQ3.js?t=764877"></script>')


def programs(kind: str | None = None, status: str | None = None) -> dict[str, dict]:
    out = {}
    for pid, p in PROGRAMS.items():
        if kind and kind not in p.get("kinds", []):
            continue
        if status and p.get("status") != status:
            continue
        out[pid] = p
    return out


def _tp_links(kinds) -> list[tuple[str, str, str, str]]:
    """Tracked Travelpayouts links for the requested kinds.

    Only brands whose partnership is live appear here; their short/long URLs were generated
    through the partner API (`createPartnerLink`) and carry marker 793747 + source 589091, so
    every click is attributed. Brands we are not joined to yet are simply absent."""
    out = []
    if TP["status"] != "approved":
        return out
    for bid, b in TP_BRANDS.items():
        if kinds and not (set(kinds) & set(b["kinds"])):
            continue
        href = b.get("short") or b.get("full")
        if not href:
            continue
        out.append((b["label"], href, "sponsored nofollow noopener", b.get("note", "")))
    return out


def links_for(slug: str, kind: str | None = None) -> list[tuple[str, str, str, str]]:
    """Return placements for one site slug (optionally narrowed to one placement kind).

    Each item is ``(label, href, rel, note)``; only links that carry our tracking id are
    returned, so a page never shows a dead/untracked partner link.
    """
    if not MONETIZATION_ON:
        return []
    site = SITES.get(slug)
    if site is None:
        return []
    kinds = [kind] if kind else site["kinds"]
    kinds = [k for k in kinds if k in site["kinds"]]
    out: list[tuple[str, str, str, str]] = []

    # 1) Travelpayouts brands that fit this site
    out += _tp_links(kinds)

    # 2) direct programmes with a referral code learned from the dashboard
    for pid, p in PROGRAMS.items():
        if p.get("status") != "approved":
            continue
        if not (set(kinds) & set(p.get("kinds", []))):
            continue
        code = AFFILIATE_CODES.get(pid)
        tpl = p.get("link_template")
        if not (code and tpl):
            continue
        href = tpl.format(code=code)
        out.append((p["name"], href, "sponsored nofollow noopener", p.get("commission", "")))
    return out


def placement_kinds(slug: str) -> list[str]:
    """Placement kinds worth wiring on a site (used by the Lead when editing page templates)."""
    site = SITES.get(slug)
    return list(site["kinds"]) if site else []


if __name__ == "__main__":  # tiny self-check: python -m engine.affiliates
    for slug in SITES:
        found = links_for(slug)
        print(f"{slug:12s} kinds={','.join(placement_kinds(slug)):60s} tracked_links={len(found)}")
    print("drive snippet:", drive_snippet())
    print("approved programs:", sorted(programs(status="approved")))
    print("pending programs :", sorted(programs(status="pending")))
    print("blocked programs :", sorted(programs(status="blocked")))
