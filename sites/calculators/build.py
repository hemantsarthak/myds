#!/usr/bin/env python3
"""Build calculators.tekify.xyz — 50 client-side calculators with live formulas.

Run:    python sites/calculators/build.py
Deploy: python scripts/ops.py deploy --project myds-calculators --dir sites/calculators/site

Every calculator is defined in calcs_*.py with its formula written twice: once in JavaScript
(what visitors run) and once in Python (server-rendered initial result + cross-check).
`check_formulas.py` runs both under node/python against the same inputs and fails on any
mismatch, so the initial HTML and the live result always agree.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from engine.sitegen import Site, cards, faq, esc, human  # noqa: E402
from engine.guides import add_guides  # noqa: E402

import catalog  # noqa: E402
from core import (CALC_CSS, RUNTIME_JS, defaults, fmt_val, page_body, word_count)  # noqa: E402

DOMAIN = "calculators.tekify.xyz"
BRAND = "Calculators"

HOME_JS = r"""
(function () {
  var q = document.getElementById('q');
  if (!q) return;
  var items = [].slice.call(document.querySelectorAll('#tools a[data-k]'));
  var count = document.getElementById('count');
  q.addEventListener('input', function () {
    var v = q.value.trim().toLowerCase(), shown = 0;
    items.forEach(function (a) {
      var hit = !v || a.getAttribute('data-k').indexOf(v) >= 0;
      a.style.display = hit ? '' : 'none';
      if (hit) shown++;
    });
    if (count) count.textContent = shown + ' of ' + items.length + ' calculators';
  });
})();
"""


def page_search_index(calcs):
    """Single small JS index for the home page filter — inline, no fetch."""
    return ""


def build() -> Site:
    cats = catalog.CATS
    by = catalog.BY
    calcs = catalog.CALCS
    group = {c["id"]: [] for c in cats}
    for c in calcs:
        group[c["cat"]].append(c)

    site = Site("calculators", BRAND, DOMAIN,
                "Free, fast calculators for loans, investing, salary, health, dates and conversions.",
                "Free online calculators with instant results: loan and mortgage payments, compound "
                "interest, retirement, take-home pay, BMI, calorie needs, dates and unit conversions.",
                nav=[("Loans", "/loans/"), ("Investing", "/investing/"), ("Salary & Tax", "/salary/"),
                     ("Health", "/health/"), ("Dates", "/dates/"), ("Converters", "/conversions/")],
                source_note="Every calculator shows its formula, a worked example and common "
                           "mistakes. Results are estimates — verify anything financial or medical "
                           "with a qualified professional.")

    # ---------------------------------------------------------------- home
    tool_cards = "".join(
        f'<a href="/{c["slug"]}/" data-k="{esc((c["name"] + " " + c["desc"] + " " + c["cat"]).lower())}">'
        f'{esc(c["name"])} <span class="mut">{esc(c["desc"].split(".")[0])}</span></a>'
        for c in sorted(calcs, key=lambda x: (x["cat"], x["name"])))
    cat_cards = cards([(f"/{c['id']}/", esc(c["name"]), human(len(group[c["id"]])) + " tools")
                       for c in cats])
    home = f"""
<h1>Free calculators — instant, no sign-up</h1>
<p class="lede">Loan payments, compound interest, take-home pay, BMI, dates and unit conversions.
Every calculator shows the formula and a worked example, and updates as you type.
<span class="stat">{len(calcs)} calculators</span><span class="stat">{len(cats)} categories</span></p>
<input type="search" id="q" placeholder="Search calculators — mortgage, BMI, overtime, tip…" autocomplete="off" autofocus>
<p class="mut" id="count">{len(calcs)} of {len(calcs)} calculators</p>
<div class="grid" id="tools">{tool_cards}</div>
<h2>Browse by category</h2>
{cat_cards}
<h2>How these calculators work</h2>
<p>Each tool is a self-contained page with a form and a live result. The arithmetic runs in your
browser — nothing you type is sent anywhere — and the same formula is printed on the page so you
can check it yourself. The server-rendered result means the page shows a useful answer even before
the script runs.</p>
<h2>Why the numbers can differ elsewhere</h2>
<p>Calculators disagree when they use different assumptions: tax years, compounding frequency,
rounding, or extras such as fees and insurance. Each page here states its assumptions and shows a
worked example with the default inputs, so you can see exactly what is included.</p>
"""
    site.add("/", "Free Online Calculators — Loans, Investing, Salary, Health & Dates",
             "50 free calculators with instant results: loan and mortgage payments, compound "
             "interest, retirement, take-home pay, BMI, pregnancy dates and unit conversions.",
             home, extra_head='<link rel="stylesheet" href="/assets/calc.css">')
    site.add_file("/assets/home.js", HOME_JS)

    # ---------------------------------------------------------------- categories
    for c in cats:
        tools = sorted(group[c["id"]], key=lambda x: x["name"])
        body = f"""
<h1>{esc(c["name"])} calculators</h1>
<p class="lede">{c["lede"]}</p>
{cards([(f'/{t["slug"]}/', esc(t["name"]), esc(t["desc"].split(".")[0])) for t in tools])}
<h2>What you can calculate</h2>
{c["intro"]}
{faq([("Are these calculators free?", "Yes. Every calculator on this site is free, needs no "
       "account and runs entirely in your browser."),
      ("How accurate are the results?",
       "Each page states its assumptions and shows a worked example. The formulas are standard "
       "industry formulas, but real-world results depend on fees, taxes and individual "
       "circumstances."),
      ("Do you store what I type?",
       "No. The calculation runs in your browser and nothing is submitted to a server.")])}
<div class="rel"><h2>Other categories</h2><p>{" · ".join(
            f'<a href="/{o["id"]}/">{esc(o["name"])}</a>' for o in cats if o["id"] != c["id"])}</p></div>
"""
        site.add(f"/{c['id']}/", c["title"], c["desc"], body,
                 crumbs=[(c["name"], None)],
                 extra_head='<link rel="stylesheet" href="/assets/calc.css">')

    # ---------------------------------------------------------------- tool pages
    words = []
    for c in calcs:
        body = page_body(c, catalog.CAT_BY[c["cat"]]["name"], by)
        site.add(f'/{c["slug"]}/', c["title"], c["desc"], body,
                 crumbs=[(catalog.CAT_BY[c["cat"]]["name"], f'/{c["cat"]}/'), (c["name"], None)],
                 extra_head='<link rel="stylesheet" href="/assets/calc.css">')
        words.append((c["slug"], word_count(
            c["lede"] + c["how"] + c["formula"] + c["example"] + " ".join(c["mistakes"]) +
            " ".join(q + " " + a for q, a in c["faq"]))))

    site.add_file("/assets/calc.css", CALC_CSS)
    site.add_file("/assets/calc.js", RUNTIME_JS)
    site.add_standard_pages(
        extra_about="<h2>How pages are built</h2><p>Each calculator is a single HTML page. "
                    "The formula is implemented once in JavaScript for the live result and once in "
                    "Python for the server-rendered answer shown before scripts run; an automated "
                    "check runs both implementations against the same inputs and fails the build if "
                    "they disagree. Pages state their assumptions, show a worked example and list "
                    "common mistakes.</p><h2>Not professional advice</h2><p>Financial, tax and "
                    "health results are estimates for planning. Consult a qualified professional "
                    "before making decisions with legal, tax or medical consequences.</p>")
    short = [s for s, n in words if n < 240]
    if short:
        print("WARN short tool pages (<240 words):", ", ".join(short[:10]), f"({len(short)} total)")
    print("word count range:", min(n for _s, n in words), "-", max(n for _s, n in words))
    add_guides(site)
    return site


if __name__ == "__main__":
    site = build()
    out = site.write()
    ok = site.validate(max_files=19900)
    print("wrote", out, "->", len(site.pages), "pages,", len(site.extra_files), "extra files")
    raise SystemExit(0 if ok else 1)
