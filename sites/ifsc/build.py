#!/usr/bin/env python3
"""Build ifsc.tekify.xyz — an IFSC code directory for every Indian bank branch.

Input : ../../.cache/ifsc.csv  (Razorpay IFSC release, MIT; see fetch_data.py)
Output: site/  (~16k static pages, deployable to Cloudflare Pages)

Pages
  /                          search + stats + browse
  /ifsc/<IFSC>/              one page per branch (payload pages, selected by city rank)
  /bank/<CODE>/              one page per bank (1,349)
  /state/<state>/            one page per state/UT (43)
  /city/<city>-<state>/      top ~700 cities by branch count
  /search/                   full-branch search (loads a compact JSON index)
  /about/ /privacy/ /contact/

Data files
  /data/branches.json        compact index of the branches that have static pages
  /data/bank/<CODE>.json     all branches of a bank (banks with >= 100 branches)
"""
import collections
import csv
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.sitegen import Site, table, cards, related, faq, esc, slug, human, notice  # noqa: E402
from engine.guides import add_guides  # noqa: E402

PROJ = pathlib.Path(__file__).resolve().parent
SITE = "https://ifsccodes.tekify.xyz"
BRAND = "IFSC Codes India"
JSONLD_BANK_ORGANIZATION = None

BRANCH_LIMIT = 18500        # static branch pages (Pages Free: 20k files/site total)
CITY_LIMIT = 700            # city pages
BANK_JSON_MIN = 100         # ship per-bank JSON for banks with at least this many branches


def clean(s) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def titlecase(s: str) -> str:
    """MAHARASHTRA -> Maharashtra, but keep small words sensible."""
    s = clean(s).lower()
    if not s:
        return ""
    small = {"and", "of", "the", "in", "on", "for"}
    parts = []
    for i, w in enumerate(s.split()):
        parts.append(w if (w in small and i) else (w[:1].upper() + w[1:]))
    return " ".join(parts)


def load() -> list[dict]:
    path = ROOT / ".cache" / "ifsc.csv"
    if not path.exists():
        sys.exit("missing .cache/ifsc.csv — run: python sites/ifsc/fetch_data.py")
    rows, seen = [], set()
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            ifsc = clean(row.get("IFSC")).upper()
            if not re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", ifsc) or ifsc in seen:
                continue
            seen.add(ifsc)
            rows.append({
                "ifsc": ifsc,
                "bank": clean(row.get("BANK")),
                "branch": clean(row.get("BRANCH")),
                "centre": clean(row.get("CENTRE")),
                "city": clean(row.get("CITY")) or clean(row.get("CENTRE")) or clean(row.get("DISTRICT")),
                "district": clean(row.get("DISTRICT")),
                "state": titlecase(row.get("STATE")),
                "address": clean(row.get("ADDRESS")),
                "contact": clean(row.get("CONTACT")),
                "micr": clean(row.get("MICR")),
                "swift": clean(row.get("SWIFT")),
                "neft": clean(row.get("NEFT")).lower() == "true",
                "rtgs": clean(row.get("RTGS")).lower() == "true",
                "imps": clean(row.get("IMPS")).lower() == "true",
                "upi": clean(row.get("UPI")).lower() == "true",
            })
    # Bank names: most common non-empty name per 4-letter bank code.
    names = collections.defaultdict(collections.Counter)
    for r in rows:
        if r["bank"]:
            names[r["ifsc"][:4]][r["bank"]] += 1
    for r in rows:
        code = r["ifsc"][:4]
        r["bank_code"] = code
        r["bank"] = names[code].most_common(1)[0][0] if names[code] else code
        r["state"] = r["state"] or "India"
        r["city"] = r["city"] or r["district"] or "India"
    return rows


def build() -> Site:
    rows = load()
    by_bank = collections.defaultdict(list)
    by_state = collections.defaultdict(list)
    by_city = collections.defaultdict(list)          # (state, city) -> rows
    for r in rows:
        by_bank[r["bank_code"]].append(r)
        by_state[r["state"]].append(r)
        by_city[(r["state"], r["city"])].append(r)
    city_rank = {k: i for i, (k, v) in enumerate(
        sorted(by_city.items(), key=lambda kv: (-len(kv[1]), kv[0])))}
    bank_rank = {k: i for i, (k, v) in enumerate(
        sorted(by_bank.items(), key=lambda kv: (-len(kv[1]), kv[0])))}

    # ---- choose which branches get a static page: densest cities first
    pages_for: list[dict] = []
    for (state, city), group in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]]):
        for r in group:
            if len(pages_for) >= BRANCH_LIMIT:
                break
            pages_for.append(r)
        if len(pages_for) >= BRANCH_LIMIT:
            break
    page_set = {r["ifsc"] for r in pages_for}
    city_page_set = {k for k, _ in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]])[:CITY_LIMIT]}
    for r in rows:
        r["has_page"] = r["ifsc"] in page_set

    s = Site(
        "ifsc", BRAND, "ifsccodes.tekify.xyz",
        "Every Indian bank branch's IFSC code — address, MICR, and supported transfer rails.",
        "Look up any Indian bank IFSC code: branch address, city, district, state, MICR code, "
        "SWIFT code and whether NEFT, RTGS, IMPS and UPI are supported. 183,000+ branches.",
        nav=[("Search", "/search/"), ("Banks", "/#banks"), ("States", "/#states"), ("About", "/about/"), ("Guides", "/guides/")],
        source_note="Data: public IFSC dataset maintained by Razorpay (MIT licence), derived from NPCI/RBI bank listings.",
    )

    # ---------------------------------------------------------------- home
    top_banks = sorted(by_bank.items(), key=lambda kv: -len(kv[1]))[:36]
    states_sorted = sorted(by_state.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    home = f"""
<h1>IFSC codes for Indian bank branches</h1>
<p class="lede">Look up the IFSC code of any branch — or paste a code to see the bank, branch,
address, MICR/SWIFT codes and which transfer rails it supports.
<span class="stat">{human(len(rows))} branches</span>
<span class="stat">{human(len(by_bank))} banks</span>
<span class="stat">{human(len(by_city))} cities</span>
<span class="stat">{len(by_state)} states</span></p>
<input type="search" id="q" placeholder="Paste an IFSC code, or type a branch, bank or city…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<h2 id="banks">Browse by bank</h2>
{cards([(f"/bank/{code}/", esc(v[0]["bank"]), human(len(v))) for code, v in top_banks])}
<p class="mut"><a href="#states">All states ↓</a></p>
<h2>What is an IFSC code?</h2>
<p>An IFSC (Indian Financial System Code) is the 11-character code that identifies a single bank
branch for electronic transfers in India. The first four characters are the bank code, the fifth
character is <code>0</code> (reserved), and the last six characters identify the branch. NEFT, RTGS,
IMPS and UPI all route payments using it.</p>
{notice("Every page on this site is generated from a public dataset. Codes change when banks "
        "merge or rename branches — confirm large transfers with the bank.")}
<h2 id="states">Browse by state</h2>
{cards([(f"/state/{slug(st)}/", esc(st), human(len(v))) for st, v in states_sorted])}
<h2>Popular city directories</h2>
{cards([(f"/city/{slug(c)}-{slug(st)}/", esc(c), human(len(v)))
        for (st, c), v in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]])[:30]])}
"""
    s.add("/", "IFSC Codes — Search Any Indian Bank Branch IFSC Code",
          "Search 183,000+ Indian bank branches by IFSC code, branch, bank or city. See address, "
          "MICR code, SWIFT code and NEFT/RTGS/IMPS/UPI support.", home)

    # ---------------------------------------------------------------- search page
    s.add("/search/", "Search IFSC Codes — Branch, Bank, City or Code",
          "Full-text search across 183,000 Indian bank branches by IFSC code, branch name, bank, "
          "city or district. Results link to the branch page.",
          """<h1>Search IFSC codes</h1>
<p class="lede">Type an IFSC code, a branch name, a bank or a city. The full index loads once,
then searches locally.</p>
<input type="search" id="q" placeholder="HDFC0000123, Andheri, HDFC Bank…" autocomplete="off" autofocus>
<div id="res" class="res"></div>
<p class="mut" id="status">Loading index…</p>""",
          crumbs=[("Search", None)])

    # ---------------------------------------------------------------- bank pages
    name_counts = collections.Counter(r["bank"] for r in rows)
    for code, group in sorted(by_bank.items(), key=lambda kv: bank_rank[kv[0]]):
        name = group[0]["bank"]
        bank_title = (f"{name} IFSC Codes — All Branches and Codes" if name_counts[name] == 1
                      else f"{name} ({code}) IFSC Codes — All Branches")
        states_in = sorted({r["state"] for r in group})
        cities_in = collections.Counter((r["state"], r["city"]) for r in group)
        top_cities = sorted(cities_in.items(), key=lambda kv: (-kv[1], kv[0]))[:24]
        sample = sorted(group, key=lambda r: (r["city"], r["branch"]))[:120]
        rows_html = table(
            ["IFSC", "Branch", "City", "State"],
            [[f'<a href="/ifsc/{r["ifsc"]}/">{r["ifsc"]}</a>' if r["has_page"] else r["ifsc"],
              r["branch"], r["city"], r["state"]] for r in sample])
        cross = [r for r in group if not r["has_page"]][:0]
        body = f"""
<h1>{esc(name)} IFSC codes</h1>
<p class="lede">{esc(name)} has {human(len(group))} branches in this directory across
{len(states_in)} states and {human(len(cities_in))} cities. Pick a branch below, or search the
whole directory for a code.</p>
<p><a href="/search/">Search all banks →</a></p>
{rows_html}
{'<p class="mut">Showing the first 120 branches. Use the search page for the rest.</p>' if len(group) > 120 else ''}
<h2>Cities with {esc(name)} branches</h2>
{cards([(f"/city/{slug(c)}-{slug(st)}/", esc(c), human(n)) for (st, c), n in top_cities if (st, c) in city_page_set])}
<h2>States</h2>
{cards([(f"/state/{slug(st)}/", esc(st), human(sum(1 for r in group if r["state"] == st))) for st in states_in])}
<h2>About {esc(name)} IFSC codes</h2>
<p>The bank code for {esc(name)} in the IFSC system is <strong>{esc(code)}</strong> — every
{esc(name)} IFSC code starts with it. The remaining characters identify the individual branch.
Use the tables above to find the exact code, then quote it to the sender for NEFT, RTGS, IMPS or UPI.</p>
"""
        s.add(f"/bank/{code}/", bank_title,
              f"All {human(len(group))} {name} branches with IFSC codes, city and state. Find the "
              f"right {name} IFSC code for NEFT, RTGS, IMPS or UPI transfers.",
              body, crumbs=[("Banks", None), (name, None)])
        if len(group) >= BANK_JSON_MIN:
            s.add_file(f"/data/bank/{code}.json", json.dumps(
                [[r["ifsc"], r["branch"], r["city"], r["state"]] for r in group],
                separators=(",", ":"), ensure_ascii=False))

    # ---------------------------------------------------------------- state pages
    for st, group in sorted(by_state.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        banks_here = collections.Counter(r["bank"] for r in group)
        cities_here = collections.Counter(r["city"] for r in group)
        top_cities = sorted(cities_here.items(), key=lambda kv: (-kv[1], kv[0]))[:40]
        body = f"""
<h1>IFSC codes in {esc(st)}</h1>
<p class="lede">{human(len(group))} bank branches across {len(banks_here)} banks and
{human(len(cities_here))} cities in {esc(st)}. Browse by bank or city, or search a code.</p>
<h2>Banks in {esc(st)}</h2>
{cards([(f"/bank/{code}/", esc(bname), human(n)) for bname, n in sorted(banks_here.items(), key=lambda kv: -kv[1])[:36]])}
<h2>Cities in {esc(st)}</h2>
{cards([(f"/city/{slug(c)}-{slug(st)}/", esc(c), human(n)) for c, n in top_cities if (st, c) in city_page_set])}
<h2>How IFSC works in {esc(st)}</h2>
<p>Every bank branch in {esc(st)} has a unique 11-character IFSC code. The code is printed on
cheque books, passbooks and account statements, and it is what you give a payer for NEFT,
RTGS, IMPS or UPI transfers. The branch directory above links to individual codes with full
addresses and MICR numbers.</p>
"""
        s.add(f"/state/{slug(st)}/", f"IFSC Codes in {st} — All Banks &amp; Branches",
              f"{human(len(group))} IFSC codes for bank branches in {st}, India. Browse branches by "
              f"bank or city and find the exact code for transfers.",
              body, crumbs=[("States", None), (st, None)])

    # ---------------------------------------------------------------- city pages
    for (st, city), group in sorted(by_city.items(), key=lambda kv: city_rank[kv[0]])[:CITY_LIMIT]:
        banks_here = collections.Counter(r["bank"] for r in group)
        sample = sorted([r for r in group if r["has_page"]], key=lambda r: r["branch"])[:150]
        rows_html = table(["IFSC", "Bank", "Branch"],
                          [[f'<a href="/ifsc/{r["ifsc"]}/">{r["ifsc"]}</a>', r["bank"], r["branch"]]
                           for r in sample]) if sample else ""
        body = f"""
<h1>IFSC codes for banks in {esc(city)}, {esc(st)}</h1>
<p class="lede">{human(len(group))} branches of {len(banks_here)} banks in {esc(city)}.
Find the branch code you need for a transfer.</p>
<h2>Banks in {esc(city)}</h2>
{cards([(f"/bank/{r['bank_code']}/", esc(r["bank"]), human(sum(1 for x in group if x["bank_code"] == r["bank_code"])))
        for r in sorted(group, key=lambda r: bank_rank[r["bank_code"]])[:30]])}
{rows_html}
<h2>How to find the right {esc(city)} IFSC code</h2>
<p>Match the branch name on your account statement to the rows above, or search by code. If your
branch is not listed, open the bank page and search that bank's branches. The 11-character code
is printed on the first page of most passbooks.</p>
{related([(f"/state/{slug(st)}/", f"All IFSC codes in {st}")])}
"""
        s.add(f"/city/{slug(city)}-{slug(st)}/",
              f"IFSC Codes in {city}, {st} — Bank Branches",
              f"IFSC codes for {human(len(group))} bank branches in {city}, {st}. Addresses, MICR "
              f"codes and branch details for NEFT, RTGS and IMPS transfers.",
              body, crumbs=[("States", "/#states"), (st, f"/state/{slug(st)}/"), (city, None)])

    # ---------------------------------------------------------------- branch pages
    for r in pages_for:
        rails = [n for n, ok in (("NEFT", r["neft"]), ("RTGS", r["rtgs"]), ("IMPS", r["imps"]), ("UPI", r["upi"])) if ok]
        rows_same_city = [x for x in by_city[(r["state"], r["city"])]
                          if x["has_page"] and x["ifsc"] != r["ifsc"]]
        rows_same_city.sort(key=lambda x: (x["bank_code"] != r["bank_code"], x["branch"]))
        nearby = rows_same_city[:10]
        bank_group = by_bank[r["bank_code"]]
        rows_html = table(["Field", "Value"], [
            ["IFSC code", f'<strong>{esc(r["ifsc"])}</strong>'],
            ["Bank", esc(r["bank"])],
            ["Branch", esc(r["branch"] or "—")],
            ["Address", esc(r["address"] or "—")],
            ["City / centre", esc(r["city"])],
            ["District", esc(r["district"] or "—")],
            ["State", f'<a href="/state/{slug(r["state"])}/">{esc(r["state"])}</a>'],
            ["MICR code", esc(r["micr"] or "—")],
            ["SWIFT code", esc(r["swift"] or "—")],
            ["Contact", esc(r["contact"] or "—")],
            ["Supported transfers", ", ".join(rails) or "—"],
        ])
        nearby_html = cards([(f'/ifsc/{x["ifsc"]}/', esc(x["branch"] or x["ifsc"]), esc(x["bank"])) for x in nearby])
        body = f"""
<h1>{esc(r["ifsc"])} — {esc(r["bank"])}, {esc(r["branch"] or r["city"])}</h1>
<p class="lede">{esc(r["ifsc"])} is the IFSC code for the {esc(r["branch"] or r["city"])} branch of
{esc(r["bank"])} in {esc(r["city"])}, {esc(r["state"])}. Use it for NEFT, RTGS, IMPS and UPI
transfers to this branch.</p>
{rows_html}
<h2>Branch summary</h2>
<p>The {esc(r["bank"])} {esc(r["branch"] or r["city"])} branch is located at
{esc(r["address"] or r["city"])}{(", " + esc(r["district"])) if r["district"] else ""},
{esc(r["state"])}. In the IFSC system the bank is identified by the prefix
<strong>{esc(r["bank_code"])}</strong>, so every {esc(r["bank"])} branch code begins with
{esc(r["bank_code"])}. The fifth character of an IFSC code is always a zero, which is why
{esc(r["ifsc"])} reads <code>{esc(r["ifsc"][:4])}0{esc(r["ifsc"][5:])}</code>.</p>
{('<p>This branch reports support for <strong>' + ", ".join(rails) + '</strong> transfers.</p>') if rails else ''}
<h2>Other branches in {esc(r["city"])}</h2>
{nearby_html or '<p>No other indexed branches in this city yet.</p>'}
{related([(f'/bank/{r["bank_code"]}/', f'All {r["bank"]} IFSC codes'),
          (f'/city/{slug(r["city"])}-{slug(r["state"])}/', f'All IFSC codes in {r["city"]}'),
          (f'/state/{slug(r["state"])}/', f'All IFSC codes in {r["state"]}')])}
{faq([
    (f'What is the IFSC code of {r["bank"]} {r["branch"] or r["city"]} branch?',
     f'The IFSC code is <strong>{esc(r["ifsc"])}</strong>. It identifies the {esc(r["branch"] or r["city"])} branch of {esc(r["bank"])} in {esc(r["city"])}, {esc(r["state"])}.'),
    (f'Where is the {r["bank"]} {r["branch"] or r["city"]} branch located?',
     f'At {esc(r["address"] or r["city"])}' + (f', {esc(r["district"])}' if r["district"] else '') + f', {esc(r["state"])}.'),
    ('Does this branch support NEFT, RTGS, IMPS or UPI?',
     (('Yes — ' + ", ".join(rails) + ' are listed as supported for this branch.') if rails
      else 'The dataset does not list transfer rails for this branch; confirm with the bank.')),
])}
"""
        s.add(f'/ifsc/{r["ifsc"]}/',
              f'{r["ifsc"]} — {r["bank"]} {r["branch"]} IFSC Code, {r["city"]}',
              f'{r["ifsc"]} is the IFSC code of the {r["bank"]} {r["branch"] or r["city"]} branch in '
              f'{r["city"]}, {r["state"]}. Address: {r["address"][:80]}. MICR {r["micr"] or "n/a"}.',
              body, crumbs=[("Banks", "/#banks"), (r["bank"], f'/bank/{r["bank_code"]}/'),
                            (r["city"], f'/city/{slug(r["city"])}-{slug(r["state"])}/'),
                            (r["ifsc"], None)])

    # ---------------------------------------------------------------- data + assets
    s.add_file("/data/branches.json", json.dumps(
        [[r["ifsc"], r["branch"], r["city"], r["state"], r["bank"], 1 if r["has_page"] else 0]
         for r in pages_for], separators=(",", ":"), ensure_ascii=False))
    s.add_file("/assets/app.js", JS)

    s.add_standard_pages(
        extra_about=f"<h2>Data</h2><p>{human(len(rows))} branches, {human(len(by_bank))} banks, "
                    f"{human(len(by_city))} cities. Source: the open IFSC dataset maintained by "
                    f"Razorpay (MIT licence), which is compiled from bank branch listings. "
                    f"Branch codes change when banks merge — always confirm large transfers.</p>")
    add_guides(s)
    return s


JS = r"""
(function(){
  var q=document.getElementById('q'), res=document.getElementById('res'), st=document.getElementById('status');
  if(!q) return;
  var idx=null, loading=false;
  function load(){
    if(idx||loading) return;
    loading=true;
    fetch('/data/branches.json').then(function(r){return r.json()}).then(function(d){
      idx=d; loading=false; if(st) st.textContent=d.length.toLocaleString()+' branches with pages; full lookup runs on paste.';
    }).catch(function(){ loading=false; });
  }
  q.addEventListener('focus', load);
  function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}
  function render(list){
    if(!list.length){res.innerHTML='<p class="mut">No match. Try a different code, branch or city.</p>';return;}
    res.innerHTML='<div class="grid">'+list.slice(0,30).map(function(r){
      if(r.length===6 && r[5]===1) return '<a href="/ifsc/'+r[0]+'/">'+r[0]+' <span class="mut">'+esc(r[1])+', '+esc(r[2])+'</span></a>';
      return '<span style="padding:10px 12px">'+esc(r[0])+' <span class="mut">'+esc(r[1])+'</span></span>';
    }).join('')+'</div>';
  }
  function lookupCode(code){
    code=code.toUpperCase();
    var bank=code.slice(0,4);
    res.innerHTML='<p class="mut">Looking up '+esc(code)+'…</p>';
    fetch('/data/bank/'+bank+'.json').then(function(r){ if(!r.ok) throw 0; return r.json(); }).then(function(d){
      var hit=d.filter(function(x){return x[0]===code})[0];
      if(hit){ location.href='/ifsc/'+code+'/'; }
      else res.innerHTML='<p>No branch found for <strong>'+esc(code)+'</strong> in this directory. Check the code, or browse <a href="/bank/'+bank+'/">bank '+esc(bank)+'</a>.</p>';
    }).catch(function(){
      res.innerHTML='<p>No branch found for <strong>'+esc(code)+'</strong>. Check the code or <a href="/search/">search by name</a>.</p>';
    });
  }
  function run(){
    var v=q.value.trim();
    if(/^[A-Za-z]{4}0[A-Za-z0-9]{6}$/.test(v)){ lookupCode(v); return; }
    if(!idx){ load(); return; }
    var s=v.toLowerCase();
    render(idx.filter(function(r){ return (r[0]+' '+r[1]+' '+r[2]+' '+r[3]+' '+r[4]).toLowerCase().indexOf(s)>=0; }));
  }
  var t; q.addEventListener('input', function(){ clearTimeout(t); t=setTimeout(run,160); });
  if(idx) run();
})();
"""


if __name__ == "__main__":
    site = build()
    out = site.write()
    ok = site.validate(max_files=19900)
    print("wrote", out, len(site.pages), "pages,", len(site.extra_files), "extra files")
    raise SystemExit(0 if ok else 1)
