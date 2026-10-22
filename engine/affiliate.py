#!/usr/bin/env python3
"""engine/affiliate.py — render one tasteful, legally-clear affiliate card.

    from engine.affiliate import affiliate_block, affiliate_block_for_site
    affiliate_block("travel")                  # -> HTML string ("" when nothing is tracked)
    affiliate_block_for_site("airports")       # -> one or more cards for that site

Design rules (deliberate, keep them):
* every outbound link carries ``rel="sponsored nofollow noopener"``;
* a visible disclosure line is part of the block ("Partner links — we may earn a commission…");
* no invented prices, ratings, discounts or fake reviews — only the partner's own name and
  a neutral description of what the product is;
* the card is plain HTML + a tiny scoped <style>, so it works in `engine/sitegen.py` pages
  without touching the site CSS, and it degrades to a normal list without CSS;
* when no program for that kind is approved + tracked, the function returns "" and the page
  renders unchanged (no dead links, no empty boxes).
"""
from __future__ import annotations

from engine.affiliates import MONETIZATION_ON, links_for

DISCLOSURE = ("Partner links: if you buy through these links we may earn a commission "
              "at no extra cost to you. This never changes what we recommend.")

# kind -> (card title, one-line lead-in). Keep the copy honest and product-neutral.
KIND_META = {
    "travel": ("Travel & stays",
               "Handy services for the airport you are looking at."),
    "flights": ("Flights", "Compare live prices for this route."),
    "hotels": ("Where to stay", "Hotels and stays near the airport or city you are checking."),
    "esim": ("Mobile data abroad", "Prepaid eSIM plans so you land with working data."),
    "flight_compensation": ("Delayed flight?",
                            "Services that check and claim compensation for a delayed or "
                            "cancelled flight."),
    "car_rental": ("Car rental", "Compare airport car hire."),
    "tours": ("Things to do", "Airport transfers, tickets and tours."),
    "vpn": ("Online privacy", "VPNs worth using on hotel and airport Wi-Fi."),
    "hosting": ("Hosting a site?",
                "Hosting we would use ourselves for a static or self-hosted project."),
    "vps": ("Servers & VPS", "Cloud servers for projects that outgrew shared hosting."),
    "domains": ("Domain names", "Register or transfer a domain for a new project."),
    "finance": ("Money tools", "Services our calculators' readers use next."),
    "insurance": ("Insurance", "Cover related to what this page covers."),
    "movers": ("Moving?", "Services for people relocating to this ZIP code."),
    "books": ("Related reading", "Books on this topic."),
}

_STYLE = """
.aff-card{border:1px solid #e3e6ea;border-radius:12px;padding:16px 18px;margin:26px 0;
  background:#f6f7f9;font-size:14.5px}
.aff-card h2{font-size:15px;margin:0 0 4px;letter-spacing:.01em}
.aff-card .aff-sub{margin:0 0 10px;color:#5c6472;font-size:13.5px}
.aff-card ul{margin:0;padding-left:18px}
.aff-card li{margin:6px 0}
.aff-card a{color:#1f6feb;text-decoration:none}
.aff-card a:hover{text-decoration:underline}
.aff-card .aff-note{color:#5c6472;font-size:12.5px}
.aff-card .aff-disc{margin:12px 0 0;padding-top:10px;border-top:1px solid #e3e6ea;
  color:#5c6472;font-size:12px;line-height:1.45}
@media(prefers-color-scheme:dark){
  .aff-card{background:#171a20;border-color:#252a33}
  .aff-card .aff-sub,.aff-card .aff-note,.aff-card .aff-disc{color:#9aa4b2}
  .aff-card a{color:#6ea8ff}
  .aff-card .aff-disc{border-top-color:#252a33}
}
"""


def _esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def affiliate_block(kind: str, slug: str | None = None, title: str | None = None,
                    lead: str | None = None, limit: int = 3,
                    heading: str = "h2", with_style: bool = True) -> str:
    """One affiliate card for a placement `kind` (optionally scoped to a site `slug`).

    Returns "" unless there is at least one *tracked* link — i.e. an approved program whose
    link carries our id — so this is always safe to call from a page template.
    """
    if not MONETIZATION_ON:
        return ""
    if slug:
        links = [l for l in links_for(slug, kind=kind)]
    else:  # no site given: build from the site-less travel set
        links = [l for l in links_for("airports", kind=kind)]
        links += [l for l in links_for("hub", kind=kind)]
    # de-duplicate by href, keep order
    seen, uniq = set(), []
    for item in links:
        if item[1] not in seen:
            seen.add(item[1])
            uniq.append(item)
    uniq = uniq[:limit]
    if not uniq:
        return ""

    default_title, default_lead = KIND_META.get(kind, ("Partner offers", ""))
    t = title or default_title
    sub = lead if lead is not None else default_lead
    items = []
    for label, href, rel, note in uniq:
        rel_attr = rel if "sponsored" in rel else f"sponsored nofollow noopener {rel}".strip()
        note_html = f' <span class="aff-note">{_esc(note)}</span>' if note else ""
        items.append(f'<li><a href="{_esc(href)}" rel="{_esc(rel_attr)}" target="_blank">'
                     f'{_esc(label)}</a>{note_html}</li>')
    sub_html = f'<p class="aff-sub">{_esc(sub)}</p>' if sub else ""
    style = f"<style>{_STYLE}</style>" if with_style else ""
    return (
        f'{style}'
        f'<aside class="aff-card" aria-label="{_esc(t)}">'
        f'<{heading}>{_esc(t)}</{heading}>{sub_html}'
        f'<ul>{"".join(items)}</ul>'
        f'<p class="aff-disc">{_esc(DISCLOSURE)}</p>'
        f'</aside>'
    )


def affiliate_block_for_site(slug: str, kinds: list[str] | None = None,
                             limit_per_block: int = 3) -> str:
    """All affiliate cards that make sense for a site slug, concatenated ("" when none).

    `kinds` lets the Lead restrict a page to one or two placements, e.g.
    ``affiliate_block_for_site("airports", kinds=["flight_compensation"])``.
    """
    from engine.affiliates import placement_kinds
    use = kinds or placement_kinds(slug)
    out, first = [], True
    for k in use:
        b = affiliate_block(k, slug=slug, limit=limit_per_block, with_style=first)
        if b:
            out.append(b)
            first = False
    return "".join(out)


def sponsored_attr(href: str) -> str:
    """rel attribute to use on any manually-added partner link."""
    return "sponsored nofollow noopener" if MONETIZATION_ON and href else "nofollow noopener"


if __name__ == "__main__":  # self-check: python -m engine.affiliate
    for s in ("airports", "hub", "zip", "calculators", "ifsc"):
        html = affiliate_block_for_site(s)
        print(f"{s:12s} block_bytes={len(html)}")
    print("travel block:", affiliate_block("travel", slug="airports")[:120] or "(empty — no "
          "tracked links yet)")
