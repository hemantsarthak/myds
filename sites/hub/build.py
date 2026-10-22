#!/usr/bin/env python3
"""Build the tekify.xyz hub: brand home, property directory, company pages.

Deploy:  python scripts/ops.py deploy --project hub --dir sites/hub/site
Attach:  python scripts/ops.py attach --project hub --domain tekify.xyz
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.sitegen import Site, cards, esc  # noqa: E402
from engine.affiliate import affiliate_block_for_site  # noqa: E402

PROPERTIES = [
    ("https://pincode.tekify.xyz/", "Pincode India",
     "Search 38,936 Indian post offices by pincode, district or state."),
    ("https://ifsccodes.tekify.xyz/", "IFSC Codes",
     "Indian bank IFSC branch codes: address, MICR, district, contact."),
    ("https://airportcodes.tekify.xyz/", "Airport Codes",
     "IATA / ICAO airport codes worldwide with city, country and coordinates."),
    ("https://zipcodes.tekify.xyz/", "US ZIP Codes",
     "US ZIP code directory: city, county, state, population and area."),
    ("https://areacodes.tekify.xyz/", "Area Codes",
     "Telephone area and country dialing codes with coverage maps of cities."),
    ("https://places.tekify.xyz/", "US Places",
     "US cities, towns and counties with 2023 population estimates and county assignment."),
    ("https://colleges.tekify.xyz/", "US Colleges",
     "Acceptance rates, tuition, enrollment and graduation rates for 6,000 US institutions."),
    ("https://hospitals.tekify.xyz/", "US Hospitals",
     "CMS star ratings, quality measures, services and contact details for 5,400 hospitals."),
    ("https://nursinghomes.tekify.xyz/", "US Nursing Homes",
     "CMS star ratings, staffing and inspections for 14,700 nursing homes."),
    ("https://homehealth.tekify.xyz/", "US Home Health",
     "CMS star ratings, services and quality measures for 12,400 home-health agencies."),
    ("https://calculators.tekify.xyz/", "Calculators",
     "Loan, mortgage, tax, salary, health and date calculators."),
]


def build() -> Site:
    s = Site(
        "hub", "Tekify", "tekify.xyz",
        "Free data directories and calculators, built to be fast and ad-light.",
        "Tekify publishes free reference directories — pincodes, IFSC bank codes, airport codes, "
        "ZIP codes, dialing codes — and practical calculators. No signups, no paywalls.",
        nav=[("Directories", "/#directories"), ("About", "/about/"), ("Contact", "/contact/")],
        source_note="Tekify is a network of independent reference sites funded by advertising.",
    )
    items = [(u, n, d) for u, n, d in PROPERTIES]
    body = f"""
<h1>Free reference data for everyday questions</h1>
<p class="lede">Tekify builds fast, ad-light directories from public datasets: postal codes,
bank branch codes, airport and dialing codes — plus calculators for the money and date
questions people actually type into search.</p>
<h2 id="directories">Directories</h2>
{cards(items)}
<h2>Why these sites exist</h2>
<p>Most lookups are still answered by 5–15 year old pages with broken layouts, banner
clutter and no source data. Each Tekify property takes one well-defined public dataset,
cleans it, and publishes every record as a readable page with the fields that matter —
plus the surrounding records so you can navigate without going back to search.</p>
<h2>Principles</h2>
<ul>
<li><strong>Data first.</strong> Every page is generated from a documented public dataset; sources are listed.</li>
<li><strong>Fast.</strong> Static HTML at the edge, no client-side frameworks, no cookie walls.</li>
<li><strong>Privacy.</strong> Cookie-free analytics; no accounts; no personal data collection.</li>
<li><strong>Maintained.</strong> Datasets are re-imported when sources publish updates.</li>
</ul>
"""
    body += affiliate_block_for_site("hub", kinds=["hosting", "travel"], limit_per_block=3)
    s.add("/", "Tekify — free data directories and calculators", 
          "Free, fast reference data: Indian pincodes, bank IFSC codes, airport codes, US ZIP codes, "
          "dialing codes and practical calculators.", body)
    s.add_standard_pages(
        extra_about="<h2>Properties</h2>" + cards([(u, n, d) for u, n, d in PROPERTIES]))
    return s


if __name__ == "__main__":
    site = build()
    out = site.write()
    site.validate()
    print("wrote", out, len(site.pages), "pages")
