#!/usr/bin/env python3
"""Build the tekify.xyz hub: brand home, property directory, company pages.

Deploy:  python scripts/ops.py deploy --project hub --dir sites/hub/site
Attach:  python scripts/ops.py attach --project hub --domain tekify.xyz
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from insights import build_insights
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
    ("https://dialysis.tekify.xyz/", "US Dialysis Centers",
     "CMS five-star ratings, quality measures and services for 7,400 dialysis facilities."),
    ("https://calculators.tekify.xyz/", "Calculators",
     "Loan, mortgage, tax, salary, health and date calculators."),
]


def build() -> Site:
    s = Site(
        "hub", "Tekify", "tekify.xyz",
        "Free data directories and calculators, built to be fast and ad-light.",
        "Tekify publishes free reference directories — pincodes, IFSC bank codes, airport codes, "
        "ZIP codes, dialing codes — and practical calculators. No signups, no paywalls.",
        nav=[("Directories", "/#directories"), ("Insights", "/insights/"), ("Press", "/press/"), ("About", "/about/"), ("Contact", "/contact/")],
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
    body += """
<h2 id="insights">Insights from the data</h2>
<p>Short analyses computed from the same public datasets as the directories - useful numbers, with
the method stated on every page.</p>
""" + cards([("/insights/hospital-ratings-by-state/", "Best-rated hospitals by state",
             "CMS star ratings aggregated by state."),
            ("/insights/hospitals-with-emergency-departments/", "Which hospitals have an ER?",
             "Emergency-services share by state."),
            ("/insights/hospitals-by-ownership/", "Hospital ratings by ownership",
             "Non-profit vs for-profit vs government."),
            ("/insights/nursing-home-staffing-by-state/", "Nursing-home staffing by state",
             "Where facilities are most consistently well staffed."),
            ("/insights/dialysis-ratings-nationally/", "Dialysis ratings nationally",
             "Distribution of the CMS five-star ratings."),
            ("/insights/largest-nursing-home-chains/", "Largest nursing-home chains",
             "Industry consolidation, counted by CMS data."),
            ("/insights/us-zip-codes-by-state/", "US ZIP codes by state",
             "Postal geography, counted."),
            ("/insights/airports-by-country/", "Airports by country",
             "Aviation infrastructure worldwide."),
            ("/insights/indian-bank-branches-by-state/", "Indian bank branches by state",
             "The banking network, state by state."),
            ("/insights/indian-bank-branch-networks/", "Indian bank branch networks",
             "IFSC codes counted by bank.")])
    body += """
<h2 id="scale">How big is this?</h2>
<p>Across the twelve directories there are <strong>more than 121,000 individual pages</strong>, each
generated from a documented public dataset and refreshed when the source publishes an update:
19,511 Indian bank branches, 17,759 US ZIP codes, 19,203 US places and counties, 15,056 nursing
homes, 12,777 home-health agencies, 10,181 airports, 7,809 dialysis centres, 6,954 area codes,
6,056 colleges, 5,888 hospitals and 71 calculators. Nothing is user-generated, so every record can
be traced to the agency that published it.</p>
<h2 id="developers">For developers</h2>
<p>Every directory also serves the underlying records as a compact JSON index that its search box
loads once and filters locally. No API key, no rate limit, CORS enabled:</p>
<ul>
<li><a href="https://zipcodes.tekify.xyz/data/zips.json">zipcodes.tekify.xyz/data/zips.json</a> — ZIP to city, county, time zone</li>
<li><a href="https://places.tekify.xyz/data/places.json">places.tekify.xyz/data/places.json</a> — places and counties with population</li>
<li><a href="https://hospitals.tekify.xyz/data/hospitals.json">hospitals.tekify.xyz/data/hospitals.json</a> — CMS hospital ratings</li>
<li><a href="https://nursinghomes.tekify.xyz/data/nursinghomes.json">nursinghomes.tekify.xyz/data/nursinghomes.json</a> — nursing-home ratings</li>
<li><a href="https://dialysis.tekify.xyz/data/dialysis.json">dialysis.tekify.xyz/data/dialysis.json</a> — dialysis facility ratings</li>
<li><a href="https://airportcodes.tekify.xyz/data/airports.json">airportcodes.tekify.xyz/data/airports.json</a> — airports with coordinates</li>
</ul>
<h2 id="faq">Questions</h2>
<ul>
<li><strong>Is the data free to use?</strong> Yes. The source datasets are public domain or openly
licensed (Census, CMS, NCES/IPEDS, GeoNames CC BY, OurAirports, Razorpay IFSC MIT); attribution is
stated on each site.</li>
<li><strong>How current is it?</strong> Each site names its source dataset and the reporting period on
the about page. CMS publishes updated quality data quarterly; Census estimates annually.</li>
<li><strong>Can I request a correction or removal?</strong> Yes — use the contact page; corrections
are applied at the next dataset refresh.</li>
<li><strong>Are there ads?</strong> The sites carry a small number of display-ad slots that keep them
free; there are no cookie walls, no accounts and no personal-data collection.</li>
</ul>
"""
    body += affiliate_block_for_site("hub", kinds=["hosting", "travel"], limit_per_block=3)
    s.add("/", "Tekify — free data directories and calculators", 
          "Free, fast reference data: Indian pincodes, bank IFSC codes, airport codes, US ZIP codes, "
          "dialing codes and practical calculators.", body)
    press_articles = [
        ("Open data directories: IFSC codes, ZIP codes, colleges, hospitals, nursing homes and more",
         "https://telegra.ph/Open-data-directories-IFSC-codes-ZIP-codes-colleges-hospitals-nursing-homes-and-more-10-22-2"),
        ("How to find any Indian bank branch's IFSC code",
         "https://telegra.ph/How-to-find-any-Indian-bank-branchs-IFSC-code-and-what-it-means-10-22"),
        ("How CMS star ratings work for hospitals, nursing homes and dialysis centres",
         "https://telegra.ph/How-CMS-star-ratings-work-for-hospitals-nursing-homes-and-dialysis-centres-10-22"),
        ("Free US ZIP code, place, area code and airport data — with JSON indexes",
         "https://telegra.ph/Free-US-ZIP-code-place-area-code-and-airport-data--with-JSON-indexes-10-22"),
        ("How to check a US hospital's CMS star rating before scheduling care",
         "https://telegra.ph/How-to-check-a-US-hospital-CMS-star-rating-before-scheduling-care-10-22"),
        ("Choosing a nursing home: what the CMS star rating does and does not tell you",
         "https://telegra.ph/Choosing-a-nursing-home-what-the-CMS-star-rating-does-and-does-not-tell-you-10-22"),
        ("US ZIP codes: what the five digits mean",
         "https://telegra.ph/US-ZIP-codes-what-the-five-digits-mean-and-how-to-look-one-up-10-22"),
        ("IATA vs ICAO airport codes",
         "https://telegra.ph/IATA-vs-ICAO-airport-codes-the-difference-and-where-to-look-them-up-10-22"),
    ]
    press_body = (
        "<h1>Press, publications and data sources</h1>"
        "<p class=\"lede\">Tekify builds free reference directories from open data. Our explainers are "
        "published on open platforms; every dataset is documented on the site that uses it.</p>"
        "<h2>Published explainers</h2>"
        + cards([(u, esc(t), "Telegraph") for t, u in press_articles])
        + "<h2>Where the data comes from</h2>"
        "<ul>"
        "<li>US Census Bureau: population estimates, place and county geography (public domain).</li>"
        "<li>Centers for Medicare &amp; Medicaid Services: hospital, nursing-home, home-health and "
        "dialysis quality data (public domain).</li>"
        "<li>NCES / IPEDS: college admissions, tuition, net price and graduation rates (public domain).</li>"
        "<li>GeoNames: place coordinates (CC BY 4.0); OurAirports: airport data (public domain).</li>"
        "<li>Razorpay IFSC dataset (MIT licence) for Indian bank branch codes.</li>"
        "</ul>"
        "<h2>Social and code</h2>"
        "<ul>"
        "<li>Substack: <a href=\"https://substack.com/@tekifydata\" rel=\"me\">@tekifydata</a></li>"
        "<li>GitHub: <a href=\"https://github.com/hemantsarthak/myds\" rel=\"me\">hemantsarthak/myds</a> "
        "(the build system behind these sites)</li>"
        "</ul>"
        "<h2>Contact</h2><p>Data corrections and removal requests: see <a href=\"/contact/\">contact</a>.</p>"
    )
    s.add("/press/", "Press and publications — Tekify",
          "Tekify explainers published on open platforms, plus the public datasets behind each directory.",
          press_body, crumbs=[("Press", None)])
    build_insights(s)
    s.add_standard_pages(
        extra_about="<h2>Properties</h2>" + cards([(u, n, d) for u, n, d in PROPERTIES]))
    return s


if __name__ == "__main__":
    site = build()
    out = site.write()
    site.validate()
    print("wrote", out, len(site.pages), "pages")
