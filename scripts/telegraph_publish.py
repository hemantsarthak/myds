"""Create a public Telegraph page (telegra.ph) that links to every directory.

Telegraph's API needs no account and no captcha: createAccount returns a token, createPage publishes
an anonymous article. The page lives on telegra.ph (a high-authority, Google-indexed domain) and its
outbound links are ordinary anchors — a real discovery path for Google, which currently indexes zero
pages on tekify.xyz.
"""
import json
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124"}
API = "https://api.telegra.ph"

SITES = [
    ("Tekify", "https://tekify.xyz", "Network homepage — free data directories and calculators"),
    ("IFSC Codes India", "https://ifsccodes.tekify.xyz", "Every Indian bank branch's IFSC code, address, MICR and transfer rails (19,511 pages)"),
    ("US ZIP Codes", "https://zipcodes.tekify.xyz", "US ZIP codes with city, county, time zone and neighbouring ZIPs (17,759 pages)"),
    ("US Places & Counties", "https://places.tekify.xyz", "US places and counties with 2023 population estimates and county assignment (19,203 pages)"),
    ("US Colleges", "https://colleges.tekify.xyz", "Acceptance rates, in-state/out-of-state tuition, net price by income and graduation rates (6,056 pages)"),
    ("US Hospitals", "https://hospitals.tekify.xyz", "CMS hospital star ratings and quality measures (5,888 pages)"),
    ("US Nursing Homes", "https://nursinghomes.tekify.xyz", "CMS nursing-home ratings, staffing hours and turnover (15,056 pages)"),
    ("US Home Health", "https://homehealth.tekify.xyz", "CMS home-health agency ratings and services (12,777 pages)"),
    ("US Dialysis Centers", "https://dialysis.tekify.xyz", "CMS dialysis facility five-star ratings and quality measures (7,809 pages)"),
    ("Area Codes", "https://areacodes.tekify.xyz", "NANP area codes and world dialing codes by code, city or state (6,954 pages)"),
    ("Airport Codes", "https://airportcodes.tekify.xyz", "IATA/ICAO airport codes, runways and nearby airports (10,181 pages)"),
    ("Calculators", "https://calculators.tekify.xyz", "Free loan, mortgage, retirement, salary, health and date calculators (67 pages)"),
]


def api(method, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{API}/{method}", data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def node(tag, children, attrs=None):
    n = {"tag": tag, "children": children}
    if attrs:
        n["attrs"] = attrs
    return n


def main():
    acc = api("createAccount", short_name="tekify", author_name="Tekify")
    if not acc.get("ok"):
        raise SystemExit(f"createAccount failed: {acc}")
    token = acc["result"]["access_token"]
    print("account token:", token[:12] + "…")

    content = [
        node("p", ["Free, ad-light reference directories built from open government and public "
                   "datasets. One page per record, plus plain JSON indexes for programmatic use."]),
        node("h3", ["Directories"]),
    ]
    for name, url, desc in SITES:
        content.append(node("p", [
            node("a", [name], {"href": url}),
            f" — {desc}",
        ]))
    content += [
        node("h3", ["What these are"]),
        node("p", ["Each directory turns a public dataset into a readable page per record: Indian bank "
                   "branch IFSC codes, US ZIP codes, US places and counties, college admissions and net "
                   "price, CMS hospital / nursing-home / home-health / dialysis quality ratings, area "
                   "codes and airport codes. Every site also serves a JSON index for developers."]),
        node("p", ["Sources: US Census Bureau, CMS, NCES/IPEDS, GeoNames, OurAirports, Razorpay IFSC "
                   "(MIT), and others — each site states its source and licence."]),
    ]
    page = api("createPage", access_token=token,
               title="Open data directories: IFSC codes, ZIP codes, colleges, hospitals, nursing homes and more",
               author_name="Tekify",
               content=json.dumps(content),
               return_content="true")
    if not page.get("ok"):
        raise SystemExit(f"createPage failed: {page}")
    url = page["result"]["url"]
    print("published:", url)
    (ROOT / ".cache" / "telegraph.json").write_text(json.dumps({"token": token, "url": url}), encoding="utf-8")

    # verify publicly and check the outbound link rel attribute
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", "ignore")
    print("status ok, length:", len(html))
    for needle in ("ifsccodes.tekify.xyz", "dialysis.tekify.xyz"):
        print(needle, "present:", needle in html)
    import re
    m = re.search(r'<a[^>]*href="https://tekify\.xyz"[^>]*>', html)
    print("home link tag:", m.group(0) if m else "NOT FOUND")


if __name__ == "__main__":
    main()
