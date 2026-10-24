"""engine/guides.py — hand-written explainer pages that make the data sites usable.

Why: Google evaluates a site as a whole. A directory of 19,000 data pages with no explanatory
content looks machine-made; the same directory plus accurate explainers of the underlying system
(IFSC codes, ZIP codes, counties, airport codes) looks like a reference work, earns internal
links from the home page, and picks up informational long-tail queries the data pages cannot.

Usage from a build script:

    from engine.guides import add_guides
    ...
    add_guides(site)      # adds /guides/ + one page per guide for site.slug

Add ("Guides", "/guides/") to the site nav so the section is reachable.
"""
from __future__ import annotations

from engine.sitegen import cards, esc, faq, related

GUIDES: dict[str, list[dict]] = {
    # ------------------------------------------------------------------ IFSC
    "ifsc": [
        dict(slug="what-is-ifsc-code",
             title="What Is an IFSC Code? Structure, Meaning and Where to Find It",
             desc="An IFSC code is the 11-character identifier for one Indian bank branch. What each "
                  "part means, where it is printed, and how to check it before a transfer.",
             h1="What is an IFSC code?",
             lede="IFSC stands for Indian Financial System Code — the eleven characters that tell the "
                  "banking system exactly which branch to credit.",
             body="""
<h2>The eleven characters, decoded</h2>
<p>An IFSC code is written as four letters, a zero, then six characters — for example
<code>HDFC0000123</code>. The first four letters are the bank code assigned by the RBI
(<code>HDFC</code>, <code>SBIN</code>, <code>ICIC</code>). The fifth character is always the digit
zero; it is reserved so that older and newer code formats stay distinguishable. The last six
characters identify the branch, and banks use them differently: some number branches sequentially
(<code>000123</code>), others encode the branch type or a town abbreviation.</p>
<h2>Where to find it</h2>
<p>The IFSC code is printed on the first page of a cheque book, on passbooks, and on bank account
statements. It also appears in the beneficiary details of every net-banking screen, and the bank's
own website usually lists branch codes. If you only know the branch name and city, search this site
instead — the branch page shows the code, MICR number, address and the transfer rails the branch
supports.</p>
<h2>Why the zero in the middle matters</h2>
<p>Before 2004 the fifth character had no fixed meaning. The RBI then reserved it as zero so that
any code could be validated structurally: four alphabetic characters, a zero, six alphanumeric
characters. That is why every IFSC code you will ever see has a 0 in position five, and why a code
with any other character there is simply invalid.</p>
<h2>Checking a code before you send money</h2>
<p>Two checks catch almost every mistake. First, does the code start with the right bank prefix?
Second, does the branch page show the city and branch name you expect? IFSC codes are not
secret — sharing yours is safe and necessary for receiving money. What you must never share is
your account number together with an OTP, or any PIN.</p>
""",
             faq=[("Is it safe to share my IFSC code?",
                   "Yes. The IFSC code identifies a branch, not an account, and is meant to be shared "
                   "so others can send you money."),
                  ("Can two branches share an IFSC code?",
                   "No. Each branch has exactly one IFSC code, and each code maps to one branch."),
                  ("What if the IFSC code I was given is wrong?",
                   "The transfer will usually fail or bounce back within a few days. Check the code on "
                   "the branch page here before sending, and confirm the branch name with the payee.")],
             rel=[("Search all IFSC codes", "/search/"), ("Browse by bank", "/#banks")]),

        dict(slug="how-to-find-ifsc-code",
             title="How to Find the IFSC Code of Any Bank Branch",
             desc="Four reliable ways to find a bank branch's IFSC code: cheque book, passbook, the "
                  "bank's own site, or a branch directory — plus how to verify it.",
             h1="How to find a branch's IFSC code",
             lede="Four places carry the code, in order of reliability.",
             body="""
<h2>1. Cheque book or passbook</h2>
<p>The IFSC code is printed on the first page of every cheque book and on the inside cover of most
passbooks, next to the account number and MICR code. This is the authoritative source because the
bank printed it for that specific branch.</p>
<h2>2. Account statement or net banking</h2>
<p>Download any statement as PDF: the branch code appears in the header. In net banking, open the
account details screen — the IFSC is usually listed beside the account number, and the beneficiary
screen will pre-fill it for your own accounts.</p>
<h2>3. The bank's branch locator</h2>
<p>Every large bank publishes a branch locator. Search by city and branch name; the result lists
the IFSC, MICR, address and often the branch phone number. Bank locators are updated when branches
merge or are renamed, which matters for older codes.</p>
<h2>4. A branch directory like this one</h2>
<p>Search by code, branch name, city or district. The advantage over a single bank's locator is
that you can compare branches, see which transfer rails a branch supports, and find the
neighbouring branch when a code turns out to be obsolete after a merger.</p>
<h2>Verifying before a transfer</h2>
<p>Cross-check two independent sources — typically the payee's cheque book plus the bank locator.
If the code's bank prefix does not match the bank you are paying, stop: a wrong prefix sends the
money to a different institution and the refund can take days.</p>
""",
             faq=[("Can I find an IFSC code from an account number?",
                   "No. The account number does not encode the branch in a way customers can read; "
                   "the IFSC must be obtained from the bank or a directory."),
                  ("Is the IFSC code the same as the MICR code?",
                   "No. IFSC is eleven characters used for electronic transfers; MICR is a nine-digit "
                   "code printed in magnetic ink for cheque clearing. Both identify the branch."),
                  ("Do branches change IFSC codes?",
                   "Yes, when banks merge or branches are renumbered. Old codes usually keep working "
                   "for a transition period, then stop.")],
             rel=[("Search IFSC codes", "/search/"), ("Browse by city", "/#states")]),

        dict(slug="ifsc-vs-micr-vs-swift",
             title="IFSC vs MICR vs SWIFT — What Each Code Is For",
             desc="Three bank codes that are constantly confused: IFSC for Indian electronic "
                  "transfers, MICR for cheque clearing, SWIFT/BIC for international payments.",
             h1="IFSC vs MICR vs SWIFT",
             lede="They all identify a bank branch, but they are used by different systems.",
             body="""
<h2>IFSC — Indian electronic transfers</h2>
<p>Eleven characters (four letters, a zero, six alphanumerics). Used by NEFT, RTGS, IMPS and UPI
to route a payment to one branch inside India. Every branch that can receive electronic transfers
has one.</p>
<h2>MICR — cheque clearing</h2>
<p>Nine digits, printed in magnetic ink along the bottom of a cheque: three digits for the city,
three for the bank, three for the branch. Cheque processing machines read it magnetically, which
is why it uses ink with iron oxide. MICR is about paper clearing, not about your online transfer.</p>
<h2>SWIFT / BIC — international payments</h2>
<p>Eight or eleven characters: four for the bank, two for the country, two for the location, and
optionally three for the branch. <code>HDFCINBB</code> is HDFC Bank, India, Mumbai; the extra three
characters narrow it to a branch. Foreign banks and remittance services ask for the SWIFT code
because the money leaves the Indian system and travels through correspondent banks.</p>
<h2>Which one do you need?</h2>
<p>Sending rupees to an Indian account from an Indian bank: IFSC. Writing or depositing a cheque:
nothing — the cheque already carries the MICR line. Receiving dollars from abroad, or sending money
overseas: SWIFT. A single branch has all three, and they are not interchangeable.</p>
""",
             faq=[("Can I use a SWIFT code instead of an IFSC code for NEFT?",
                   "No. Domestic transfers inside India route on IFSC; SWIFT is only used when the "
                   "payment crosses the border."),
                  ("Where is the MICR code printed?",
                   "Along the bottom of a cheque, in the magnetic-ink line, and on the first page of "
                   "most passbooks."),
                  ("Does every branch have a SWIFT code?",
                   "No. Only branches that handle international payments have one; many small "
                   "branches use the bank's head-office SWIFT code.")],
             rel=[("Search IFSC codes", "/search/"), ("Browse by bank", "/#banks")]),
    ],
    # ------------------------------------------------------------------ ZIP
    "zip": [
        dict(slug="how-zip-codes-work",
             title="How US ZIP Codes Work — Structure, Types and Limits",
             desc="ZIP codes are delivery routes, not boundaries. How the five digits are structured, "
                  "why one ZIP can span cities and counties, and what ZIP+4 adds.",
             h1="How US ZIP codes work",
             lede="A ZIP code is a mail delivery route, which is why it does not line up neatly with "
                  "city or county borders.",
             body="""
<h2>The five digits</h2>
<p>The first digit divides the country into groups of states, the next two narrow that to a
sectional centre facility, and the final two identify a delivery area — a set of carrier routes
served from one post office. Because it is a route, a single ZIP can cover parts of two cities,
and a city can be split across a dozen ZIPs.</p>
<h2>ZIP+4</h2>
<p>The four extra digits after a hyphen identify a smaller segment: one side of a street, a
building, a floor, or a group of PO boxes. ZIP+4 improves mail sorting accuracy but is optional for
most personal mail. The five-digit code is what address forms and websites normally ask for.</p>
<h2>ZIPs are not census areas</h2>
<p>The Census Bureau builds ZCTAs (ZIP Code Tabulation Areas) by snapping ZIP delivery areas to
census blocks so population can be estimated. A ZCTA approximates a ZIP but is not identical, which
is why population figures are published per ZCTA and labelled as estimates.</p>
<h2>What ZIPs do not tell you</h2>
<p>They do not define municipal boundaries, school districts, or tax jurisdictions. Two houses on
the same street can share a ZIP but sit in different cities, counties or even states. When a ZIP
appears to be in two places at once, both are usually correct — the ZIP follows mail routes, the
city follows legal boundaries.</p>
""",
             faq=[("Can one ZIP code cover two cities?",
                   "Yes. ZIP codes follow postal delivery routes, so a ZIP can include parts of "
                   "several municipalities."),
                  ("Is a ZIP code the same as a ZCTA?",
                   "No. A ZCTA is a Census Bureau statistical area built from ZIP delivery areas; "
                   "they are close but not identical."),
                  ("Do ZIP codes change?",
                   "Occasionally — the USPS adds, retires and re-draws delivery areas, usually in "
                   "fast-growing suburbs.")],
             rel=[("Look up a ZIP code", "/search/"), ("Browse ZIPs by state", "/#states")]),

        dict(slug="zip-code-vs-postal-code",
             title="ZIP Code vs Postal Code — What Other Countries Call It",
             desc="ZIP is the US brand name for a postal code. How the UK, Canada, India, Germany and "
                  "others format theirs, and why the difference matters when filling forms.",
             h1="ZIP code vs postal code",
             lede="ZIP is the American name for a postal code; every country has its own format and "
                  "its own rules.",
             body="""
<h2>United States</h2>
<p>Five digits, optionally extended with four more (<code>90210-1234</code>). Assigned by the
USPS as delivery routes.</p>
<h2>United Kingdom</h2>
<p>Alphanumeric, usually two parts — outward code and inward code — such as <code>SW1A 1AA</code>.
The outward part can cover a few dozen addresses; the inward part narrows to a street or a side of
one.</p>
<h2>Canada</h2>
<p>Six characters alternating letter-digit, such as <code>K1A 0B1</code>. The first three identify
a forward sortation area (often a whole neighbourhood), the last three a local delivery unit.</p>
<h2>India</h2>
<p>Six digits — the PIN code. The first digit is the postal zone, the second the sub-zone, the
third the sorting district, and the last three the individual post office.</p>
<h2>Germany and much of Europe</h2>
<p>Germany uses five digits (<code>10115</code>), France five, the Netherlands four plus two
letters, Switzerland four. Formats differ enough that forms should never assume a length.</p>
<h2>Why it matters</h2>
<p>When a form rejects your postal code, the cause is almost always a validation rule written for
one country's format. This directory maps US ZIP codes; for Indian PIN codes and other countries,
see the sister sites in the footer.</p>
""",
             faq=[("Is ZIP code only used in the US?",
                   "ZIP is a USPS trademark for the US system. Other countries call the same concept a "
                   "postcode, postal code, PIN code or CAP."),
                  ("Can a postal code be shorter than five characters?",
                   "Yes — several countries use four digits or fewer, and some mix letters and digits."),
                  ("Are postal codes assigned by street?",
                   "In most countries they cover a group of addresses or a delivery round, not a "
                   "single street number.")],
             rel=[("Look up a ZIP code", "/search/"), ("ZIP codes by state", "/#states")]),
    ],
    # ------------------------------------------------------------------ places
    "places": [
        dict(slug="city-town-village-cdp",
             title="City vs Town vs Village vs CDP — US Place Types Explained",
             desc="What the Census Bureau means by city, town, village, borough and Census-designated "
                  "place, and why the same place can be described differently in two datasets.",
             h1="City, town, village, borough or CDP?",
             lede="The label after a place name is a legal status, not a size ranking.",
             body="""
<h2>Incorporated places</h2>
<p>Cities, towns, villages and boroughs are incorporated: they have a charter from the state, a
government, and the power to tax and pass ordinances. Which word a state uses is a matter of
local tradition, not population. A "village" in Illinois can be larger than a "city" in another
state, and in New England a "town" is a full municipal government covering a whole area.</p>
<h2>Census-designated places (CDPs)</h2>
<p>A CDP is a settled community with no municipal government. The Census Bureau draws a boundary
around it purely so it can publish statistics. Many CDPs are suburbs or unincorporated communities
where residents rely on a county for services. If a place is labelled CDP, expect no mayor, no
city hall and no city taxes.</p>
<h2>Consolidated and unified governments</h2>
<p>Some places merged city and county government — Nashville-Davidson, Indianapolis-Marion,
Louisville-Jefferson. The Census publishes both the consolidated entity and the "balance" (the part
outside other incorporated places), which is why the same city can appear twice with different
population figures.</p>
<h2>Why this matters when you look up a place</h2>
<p>Two datasets can disagree about a place's name, type or population without either being wrong:
one may report the consolidated government, the other the balance, and a CDP may be counted
separately from the city it sits beside. Always check the type and the vintage year.</p>
""",
             faq=[("Is a CDP a real town?",
                   "It is a real community, but it has no municipal government — the Census Bureau "
                   "defines the boundary only for statistics."),
                  ("Why does one place appear with two population figures?",
                   "Consolidated city-county governments are published both as the consolidated entity "
                   "and as the balance excluding other incorporated places."),
                  ("Does a village have fewer people than a city?",
                   "Not necessarily. The label reflects state law and tradition, not size.")],
             rel=[("Search US places", "/search/"), ("Browse by state", "/#states")]),

        dict(slug="what-is-a-county",
             title="What Is a County? US County Government Explained",
             desc="Counties are the main local layer between state and city in most of the US. What "
                  "they do, why Louisiana and Alaska differ, and how to find which county a place is in.",
             h1="What is a county?",
             lede="The county is usually the oldest and most durable local boundary in the United "
                  "States.",
             body="""
<h2>What counties do</h2>
<p>Counties run courts, jails, property records, elections, public health departments and, outside
city limits, roads and policing. In many states they also assess property taxes and issue marriage
licences and permits. City governments handle municipal services inside their boundaries; the
county covers everything else.</p>
<h2>Not every state uses the word</h2>
<p>Louisiana calls its equivalents <em>parishes</em>; Alaska has <em>boroughs</em> plus a vast
"unorganized borough" with no county government at all. Connecticut, Rhode Island and parts of
Massachusetts have counties only as geographic labels, with no county government left. Puerto Rico
uses <em>municipios</em>, which function as both county and city.</p>
<h2>Counties do not move, cities do</h2>
<p>County boundaries are extremely stable — most date from the nineteenth century. City boundaries
expand constantly through annexation. That is why a house can be inside a city that grew into a
neighbouring county, and why a ZIP code (a mail route) may cross a county line while the city
does not.</p>
<h2>Finding which county a place is in</h2>
<p>Search the place here: every place page lists its primary county, and any additional counties
it extends into. County pages then list the cities, towns and CDPs inside them.</p>
""",
             faq=[("What is the difference between a county and a city?",
                   "A city is an incorporated municipality with its own government; a county is the "
                   "larger local division that provides courts, records and services across cities "
                   "and unincorporated land."),
                  ("Does every US state have counties?",
                   "Almost all do, but Louisiana has parishes, Alaska has boroughs, and some New "
                   "England counties have no government."),
                  ("Can a city be in two counties?",
                   "Yes. Annexation and geography mean many cities span a county line; the place page "
                   "here lists every county it touches.")],
             rel=[("Search US places", "/search/"), ("Browse counties by state", "/#states")]),
    ],
    # ------------------------------------------------------------------ airport
    "airport": [
        dict(slug="iata-vs-icao",
             title="IATA vs ICAO Airport Codes — What the Difference Is",
             desc="Three-letter IATA codes are for passengers, four-letter ICAO codes are for flight "
                  "planning. Why both exist, how they are assigned, and when each is used.",
             h1="IATA vs ICAO codes",
             lede="Two coding systems, two audiences: one prints on your bag tag, the other lives in "
                  "the flight plan.",
             body="""
<h2>IATA codes — three letters</h2>
<p>Assigned by the International Air Transport Association, IATA codes are the ones passengers
see: on tickets, baggage tags, departure boards and airline apps. <code>LHR</code> is Heathrow,
<code>JFK</code> is Kennedy. They are unique worldwide and are reassigned only when an airport
closes or a code is retired.</p>
<h2>ICAO codes — four letters</h2>
<p>Assigned by the International Civil Aviation Organization and used in flight plans, air traffic
control and weather reports. The first letter or two indicate the region or country —
<code>K</code> for the contiguous United States, <code>EG</code> for the United Kingdom,
<code>RJ</code> for Japan — and the rest identify the airfield. So Heathrow is <code>EGLL</code>
and Kennedy is <code>KJFK</code>.</p>
<h2>Where the systems overlap</h2>
<p>Most large airports have both codes, but small airfields, heliports, seaplane bases and private
strips often have only an ICAO or local identifier. Conversely, some codes look similar: a
three-letter IATA code and a four-letter ICAO code for the same city share no digits, so mixing
them up is a common travel-agency error.</p>
<h2>Reading a code you find here</h2>
<p>Every airport page lists the IATA code, the ICAO code, the local identifier, coordinates,
elevation and runways, so you can confirm which system you are looking at before booking or filing.</p>
""",
             faq=[("Is the IATA code the same as the ICAO code?",
                   "No. IATA codes are three letters for commercial use; ICAO codes are four letters "
                   "for aviation operations."),
                  ("Do all airports have an IATA code?",
                   "No. Only airports with commercial passenger service normally receive one; small "
                   "airfields may have only an ICAO or local code."),
                  ("Can two airports share a code?",
                   "IATA codes are unique worldwide. ICAO codes are also unique, but the same three "
                   "letters can appear inside unrelated four-letter codes.")],
             rel=[("Search airport codes", "/search/"), ("Browse by country", "/#countries")]),

        dict(slug="airport-runways-explained",
             title="Airport Runways Explained — Length, Surface, Lighting and Designators",
             desc="What runway numbers mean, why length and surface matter, how lighting enables night "
                  "operations, and how to read the runway tables on airport pages.",
             h1="How to read airport runway data",
             lede="Runway length, surface and lighting decide which aircraft can use an airport — and "
                  "in what weather.",
             body="""
<h2>Designators</h2>
<p>Runways are numbered by magnetic heading rounded to the nearest ten degrees, with the last zero
dropped: a runway pointing 090° is "09", its opposite end "27". Letters L, C and R distinguish
parallel runways (left, centre, right). When the magnetic field shifts enough, the numbers are
repainted — which is why some runways change designator every few years.</p>
<h2>Length</h2>
<p>Length is the single most important operational limit. A short runway restricts take-off weight
because an aircraft must reach flying speed before the end; at high-altitude or hot airports the
required length grows again because the air is thinner. Runway tables here give length in feet and
metres so you can compare across datasets.</p>
<h2>Surface</h2>
<p>Asphalt and concrete handle heavy jets; grass, gravel and water suit light aircraft and
seaplanes. Surface condition matters as much as type: a wet or contaminated runway increases
stopping distance, which is why grooved concrete is common at busy airports.</p>
<h2>Lighting</h2>
<p>Runway edge lights, centreline lights and approach lighting allow operations in darkness and
low visibility. A runway without lighting effectively closes at sunset for commercial traffic. The
"lighted" column on each airport page tells you which runways have it.</p>
<h2>Reading the table</h2>
<p>Each airport page lists up to six runways with length, metric length, surface, lighting and
designator — enough to judge whether an airfield suits a given aircraft without hunting through
aviation publications.</p>
""",
             faq=[("What do runway numbers mean?",
                   "They are the runway's magnetic heading divided by ten: runway 09 points roughly "
                   "east, runway 27 roughly west."),
                  ("Why does runway length matter?",
                   "Heavier aircraft need more distance to accelerate to take-off speed and to stop "
                   "after landing, so length limits weight and aircraft type."),
                  ("Can an airport operate without runway lights?",
                   "Only in daylight and good visibility; night and low-visibility operations require "
                   "lighting and often instrument approach aids.")],
             rel=[("Search airport codes", "/search/"), ("Browse by country", "/#countries")]),
    ],
    # ------------------------------------------------------------------ calculators
    "calculators": [
        dict(slug="how-loan-amortisation-works",
             title="How Loan Amortisation Works (And Why Early Payments Are Mostly Interest)",
             desc="A plain explanation of amortisation: how a fixed payment splits between interest "
                  "and principal, why the split changes, and how to use the calculators here.",
             h1="How loan amortisation works",
             lede="A fixed-rate loan has a constant payment, but what that payment buys changes every "
                  "single month.",
             body="""
<h2>The formula in words</h2>
<p>Each month the lender charges interest on whatever balance is outstanding, then applies the rest
of your payment to reducing that balance. Early on, the balance is large, so interest eats most of
the payment. Later, the balance is small, so almost all of the payment is principal. The payment
itself never changes.</p>
<h2>A worked example</h2>
<p>A $250,000 mortgage at 6% for 30 years costs $1,498.88 a month. In month one, interest is
$1,250 and principal only $248.88. By the final year the interest portion is under $30 and almost
the whole payment is principal. Over the life of the loan you pay about $289,595 in interest —
more than the amount borrowed.</p>
<h2>Why extra payments help so much</h2>
<p>An extra payment goes entirely to principal, which removes all the future interest that
principal would have generated. That compounding effect is why a modest extra monthly amount can
cut years off a mortgage; the amortisation calculator shows the schedule month by month.</p>
<h2>Using the calculators here</h2>
<p>Start with the loan or mortgage payment calculator for the headline number, then open the
amortisation calculator to see the split over time. Compare two offers with the same loan amount
and term: the difference in total interest is usually far larger than the difference in monthly
payment suggests.</p>
""",
             faq=[("Why is most of my early payment interest?",
                   "Interest is charged on the outstanding balance, which is at its largest at the "
                   "start of the loan."),
                  ("Does a lower monthly payment always mean a cheaper loan?",
                   "No. A longer term lowers the payment but raises total interest; compare total "
                   "interest, not just the monthly figure."),
                  ("Do extra payments reduce the term or the payment?",
                   "It depends on the lender. Most apply extras to principal and shorten the term "
                   "unless you ask them to recast the payment.")],
             rel=[("Loan payment calculator", "/loan-payment/"),
                  ("Mortgage amortisation", "/mortgage-amortization/")]),
        dict(slug="when-does-refinancing-pay-off",
             title="When Does Refinancing Pay Off? The Break-Even Math",
             desc="How to calculate the break-even point on a mortgage refinance: closing costs "
                  "versus monthly savings, rate-and-term versus cash-out, and when refinancing is "
                  "not worth it.",
             h1="When does refinancing pay off?",
             lede="A refinance costs money up front to save money each month. The only honest question "
                  "is how long it takes to get the upfront cost back — and whether you will still be "
                  "in the house or the loan by then.",
             body="""
<h2>The break-even calculation</h2>
<p>Divide the <strong>total cost of refinancing</strong> by the <strong>monthly payment
savings</strong>. If closing costs are $4,800 and the new payment is $160 lower, the break-even point
is <strong>30 months</strong>. Stay in the home longer than that and the refinance is ahead; sell or
refinance again sooner and you lose money on it. The break-even calculator here does the arithmetic
including points you pay to buy the rate down.</p>
<h2>What closing costs actually include</h2>
<p>Expect roughly <strong>2–5% of the loan amount</strong>: lender origination, appraisal, title
search and insurance, recording fees, and any discount points. Some costs can be rolled into the
loan, but that raises the balance and the interest you pay — roll them in and the break-even moves
out.</p>
<h2>Rate-and-term versus cash-out</h2>
<p><strong>Rate-and-term</strong> refinancing replaces the loan to get a lower rate, a shorter term,
or to drop mortgage insurance. <strong>Cash-out</strong> refinancing borrows against equity, usually
at a higher rate than rate-and-term; the monthly payment may go up even when the rate falls. Treat
cash-out as a new loan decision, not a way to "save" on the old one.</p>
<h2>When a refinance is usually worth it</h2>
<ul>
<li>The new rate is meaningfully lower — often cited as about 0.75–1 percentage point, though closing
costs and loan size matter more than the rule of thumb.</li>
<li>You will stay in the home past the break-even month.</li>
<li>You can shorten the term without straining the budget, or remove mortgage insurance.</li>
<li>Your credit and equity have improved enough to qualify for a better rate than the original loan.</li>
</ul>
<h2>When it is not</h2>
<p>If you plan to move soon, if the rate drop is small relative to costs, if the new loan restarts a
30-year term late in the current one, or if the refinance is only to lower the payment by extending
the term — that trades real total interest for temporary cash-flow relief.</p>
""",
             faq=[("How do I calculate the break-even point on a refinance?",
                   "Divide total closing costs by the monthly payment savings; the result is the "
                   "number of months before the refinance pays for itself."),
                  ("Is a cash-out refinance a good idea?",
                   "It resets the whole loan at a new rate and typically a higher one. Compare the "
                   "cash-out cost against a home-equity loan or line of credit, and treat it as a new "
                   "borrowing decision."),
                  ("How much does refinancing cost?",
                   "Usually about 2-5% of the loan amount in lender, appraisal, title and recording "
                   "costs, plus any discount points.")],
             rel=[("Refinance break-even calculator", "/refinance-breakeven/"),
                  ("Mortgage payment calculator", "/mortgage-payment/"),
                  ("Mortgage amortisation", "/mortgage-amortization/")]),
        dict(slug="how-much-house-can-i-afford",
             title="How Much House Can You Afford? The 28/36 Rule Explained",
             desc="The 28/36 rule, debt-to-income limits lenders use, how the down payment and PMI "
                  "change the maths, and the costs buyers forget when setting a budget.",
             h1="How much house can you afford?",
             lede="Lenders will often approve more than is comfortable. The 28/36 rule is a "
                  "conservative starting point; the real number depends on your other debts, savings "
                  "and how stable your income is.",
             body="""
<h2>The 28/36 rule</h2>
<p>Keep <strong>housing costs at or below 28%</strong> of gross monthly income and <strong>total
debt payments at or below 36%</strong>. On $8,000 gross monthly income that means $2,240 for
mortgage principal, interest, property tax and insurance, and no more than $2,880 in total monthly
debt. Many lenders will go to a 43–50% debt-to-income ratio for qualified buyers — approval is not
the same as affordability.</p>
<h2>What counts in housing cost</h2>
<p>Principal and interest, property taxes, homeowners insurance, mortgage insurance if the down
payment is under 20%, and HOA dues. On a $400,000 loan at 6.5% for 30 years, principal and interest
is about $2,528 a month; taxes and insurance can easily add several hundred more, and those costs
rise over time even when the mortgage payment does not.</p>
<h2>The down payment</h2>
<p>Twenty percent avoids private mortgage insurance and gives the lowest payment, but it is not
mandatory: many loan programmes allow 3–5% down for qualified buyers. A smaller down payment means
mortgage insurance, a higher payment and less equity — model both with the down-payment calculator
before deciding.</p>
<h2>The costs buyers forget</h2>
<ul>
<li>Closing costs (2–5% of the loan) and moving costs</li>
<li>Maintenance and repairs, often 1% of the home's value a year</li>
<li>Higher utilities, HOA special assessments and property-tax reassessment</li>
<li>An emergency fund that survives the purchase — do not spend it all on the down payment</li>
</ul>
<h2>Set the budget before the search</h2>
<p>Decide the monthly payment you can carry through a job loss or a rate reset, subtract the
taxes/insurance/HOA estimate, and work backwards to a purchase price. Then get pre-approved: it
tells you what a lender will actually offer, which is useful information — not a spending target.</p>
""",
             faq=[("What is the 28/36 rule?",
                   "Housing costs no more than 28% of gross monthly income and total debt payments no "
                   "more than 36%. It is a conservative budget guide, not a lending rule."),
                  ("How much down payment do I need?",
                   "Twenty percent avoids mortgage insurance and lowers the payment, but many programmes "
                   "allow 3-5% down for qualified buyers."),
                  ("Do lenders approve more than I can afford?",
                   "Sometimes. Approval is based on debt-to-income limits and credit; your own budget "
                   "should also cover savings, maintenance and irregular expenses.")],
             rel=[("Mortgage affordability calculator", "/mortgage-affordability/"),
                  ("Down payment calculator", "/down-payment-calculator/"),
                  ("Rent vs buy calculator", "/rent-vs-buy/")]),
        dict(slug="how-much-life-insurance-do-i-need",
             title="How Much Life Insurance Do You Need? The DIME Method",
             desc="A simple way to size life insurance: debts, income replacement, mortgage and "
                  "education, plus why term cover usually beats whole life for most families.",
             h1="How much life insurance do you need?",
             lede="The right amount is the number that lets the people who depend on your income keep "
                  "their standard of living. Most families need more than an employer's group policy "
                  "provides, and term insurance is usually the cheapest way to get it.",
             body="""
<h2>The DIME method</h2>
<p>Add four numbers: <strong>D</strong>ebts (credit cards, car loans, personal loans),
<strong>I</strong>ncome replacement (often 10× annual income, or enough years to cover the
children's dependency), <strong>M</strong>ortgage balance, and <strong>E</strong>ducation costs for
each child. Subtract existing savings and cover you already have. The result is a rough death
benefit — a starting point, not a precise answer.</p>
<h2>A worked example</h2>
<p>Income $75,000 (10× = $750,000), mortgage $240,000, other debts $15,000, two children's
education $120,000: about $1.13 million. With $100,000 saved and a $150,000 group policy from work,
the gap is roughly $880,000. A 20-year level term policy for that amount is often surprisingly
affordable for a healthy 30–40 year old.</p>
<h2>Term versus whole life</h2>
<p><strong>Term</strong> covers a set period (10, 20, 30 years) with no cash value — cheap per
dollar of cover, ideal when the need is temporary (until the mortgage is paid, children finish
school, retirement savings grow). <strong>Whole life and universal</strong> policies last for life,
build cash value and cost far more; they can make sense for estate planning or permanent needs, but
they are usually an expensive way to buy pure protection.</p>
<h2>Do not rely on group cover alone</h2>
<p>Employer group life is typically 1–2× salary, ends when the job ends, and is not portable. Use it
as part of the total, not the plan.</p>
<h2>Review it</h2>
<p>Reassess when you marry, have children, buy a home, change income, or when a policy term ends.
Cover that felt generous at 30 can be inadequate at 40.</p>
""",
             faq=[("How much life insurance do I need?",
                   "A common starting point is 10-12 times income plus debts and the mortgage, minus "
                   "savings and existing cover. The DIME method above shows the arithmetic."),
                  ("Is term or whole life better?",
                   "For most families with temporary needs, level term gives far more cover per dollar. "
                   "Whole life suits permanent needs and estate planning but costs much more."),
                  ("Is employer life insurance enough?",
                   "Usually not. Group cover is often 1-2 times salary and ends with the job. Treat it as "
                   "one part of the total.")],
             rel=[("Net worth calculator", "/net-worth-calculator/"),
                  ("Emergency fund calculator", "/emergency-fund-calculator/"),
                  ("Savings goal calculator", "/savings-goal/")]),
        dict(slug="debt-snowball-vs-avalanche",
             title="Debt Snowball vs Avalanche: Which Pays Off Debt Faster?",
             desc="The maths of avalanche (highest interest first) versus the motivation of snowball "
                  "(smallest balance first), plus consolidation loans and balance transfers.",
             h1="Debt snowball vs avalanche",
             lede="Two methods, one goal: get out of debt. Avalanche is mathematically cheaper; "
                  "snowball is often easier to stick with. The difference between them is usually "
                  "smaller than the difference between either and doing nothing.",
             body="""
<h2>Avalanche: highest interest rate first</h2>
<p>Pay minimums on everything, then throw every spare dollar at the <strong>highest-APR</strong>
debt. It minimises total interest paid and is the fastest route mathematically. It can be
discouraging when the target balance is large and the visible progress is slow.</p>
<h2>Snowball: smallest balance first</h2>
<p>Pay minimums everywhere, then attack the <strong>smallest balance</strong>, rolling each cleared
payment into the next debt. It costs slightly more in interest but delivers quick wins, which
research on behaviour suggests keeps people on plan.</p>
<h2>Which is better?</h2>
<p>If the rates are similar, snowball. If one card charges 29% and another 8%, avalanche — the
interest gap is worth the patience. The debt-payoff and credit-card-payoff calculators here let you
compare both orders with your real balances and see the interest difference in dollars.</p>
<h2>Consolidation and balance transfers</h2>
<p>A <strong>consolidation loan</strong> replaces several debts with one lower-rate payment. It
lowers the interest cost only if the rate is genuinely lower and you do not run the cards back up.
A <strong>0% balance-transfer card</strong> can pause interest for 12–21 months for a 3–5% fee, but
only if you can clear the balance before the promo rate ends. Read the fee, the post-promo rate and
the credit-limit terms before moving debt.</p>
<h2>The step that matters most</h2>
<p>Neither method works while new debt is being added. Fix the cash-flow gap first: a written budget,
an emergency fund of even $500–$1,000, and automatic payments. Then pick a method and automate
it.</p>
""",
             faq=[("Is avalanche or snowball better?",
                   "Avalanche saves more interest; snowball builds momentum. Pick avalanche when rates "
                   "differ a lot, snowball when the motivation gap is the real problem."),
                  ("Does debt consolidation hurt my credit?",
                   "A new loan adds a hard inquiry and can lower the average account age, but paying down "
                   "revolving balances usually helps. Effects vary - check before applying."),
                  ("Should I pay off debt or invest?",
                   "Compare the after-tax interest rate on the debt with expected investment returns, and "
                   "keep an emergency fund first. Paying a 25% credit card is a guaranteed 25% return.")],
             rel=[("Debt payoff calculator", "/debt-payoff-calculator/"),
                  ("Credit card payoff calculator", "/credit-card-payoff/"),
                  ("Loan payment calculator", "/loan-payment/")]),
        dict(slug="student-loan-repayment-plans",
             title="Student Loan Repayment Plans Explained",
             desc="Standard, graduated, extended and income-driven repayment: how each sets the "
                  "payment, which qualifies for loan forgiveness, and how to compare them.",
             h1="Student loan repayment plans explained",
             lede="The plan you choose changes the monthly payment, the total interest, and whether you "
                  "can qualify for forgiveness. Pick it deliberately — the default is not always the "
                  "cheapest.",
             body="""
<h2>Standard repayment</h2>
<p>Fixed payments over 10 years (up to $30,000 borrowed; longer if more). It is the fastest and
usually cheapest path in total interest, and the only plan where the 10-year clock for Public
Service Loan Forgiveness starts cleanly on federal Direct Loans.</p>
<h2>Graduated and extended plans</h2>
<p><strong>Graduated</strong> starts lower and rises every two years. <strong>Extended</strong>
stretches payments to 25 years for borrowers with larger balances — lower monthly cost, much more
interest over time. Both suit people early in a career who expect income growth, at the cost of
total interest.</p>
<h2>Income-driven repayment (IDR)</h2>
<p>IDR plans cap the payment at a percentage of discretionary income and forgive the remaining
balance after a set number of years (commonly 20–25, shorter in some cases). They are the safety net
for borrowers whose debt exceeds their income. The rules and the specific plan names change
frequently: check the official site (studentaid.gov) for the current plans, the income definition,
and whether forgiveness is currently taxable in your situation.</p>
<h2>Public Service Loan Forgiveness</h2>
<p>Borrowers in qualifying public-service jobs (government, many non-profits) can have the remaining
balance forgiven after <strong>120 qualifying monthly payments</strong> under a qualifying plan —
which is why the choice of repayment plan matters. Certify employment every year and keep records.</p>
<h2>How to decide</h2>
<p>Start with the standard plan's payment and total interest, then ask whether the monthly payment
fits your budget. If it does not, use the student-loan calculator to stress-test a longer term, and
consider IDR only with the forgiveness terms in writing. Refinancing private loans can lower the
rate — but refinanced federal loans lose federal protections, forgiveness eligibility and IDR
options. Never refinance federal loans without understanding that trade-off.</p>
""",
             faq=[("What is the cheapest student loan repayment plan?",
                   "Usually standard 10-year repayment, because it minimises total interest - if you can "
                   "afford the payment. Income-driven plans can cost more in total but stop a default."),
                  ("Does refinancing federal student loans lose benefits?",
                   "Yes. Refinancing with a private lender replaces federal loans and removes access to "
                   "income-driven repayment, deferment options and Public Service Loan Forgiveness."),
                  ("How do I get Public Service Loan Forgiveness?",
                   "120 qualifying monthly payments while working full time for a qualifying employer, "
                   "under a qualifying repayment plan, with employment certified each year. Verify the "
                   "current rules at studentaid.gov.")],
             rel=[("Student loan calculator", "/student-loan/"),
                  ("Loan payment calculator", "/loan-payment/"),
                  ("Budget: hourly to salary", "/hourly-to-salary/")]),
    ],
    # ------------------------------------------------------------------ colleges
    "colleges": [
        dict(slug="how-to-read-acceptance-rates",
             title="How to Read a College Acceptance Rate (And What It Does Not Tell You)",
             desc="What acceptance rate measures, why a low rate is not the same as a good college, "
                  "how yield and test-optional policies distort it, and what to compare instead.",
             h1="How to read an acceptance rate",
             lede="The acceptance rate is admitted ÷ applicants. It measures selectivity, not quality.",
             body="""
<h2>The arithmetic</h2>
<p>If 20,000 students apply and 5,000 are admitted, the acceptance rate is 25%. The figure is
reported by the institution to IPEDS and covers first-time, degree-seeking applicants for the fall
term. It says nothing about the quality of teaching, class size or outcomes — only how many
applicants the admissions office turned away.</p>
<h2>Why it can mislead</h2>
<p>Three distortions matter. First, <em>free applications</em>: when a college drops its fee or
supplemental essay, applications rise, the rate falls, and the college looks more selective without
changing who it admits. Second, <em>marketing-driven applications</em>: schools that buy names and
recruit widely lower their rate the same way. Third, <em>yield</em> — the share of admitted students
who enrol — varies hugely, so two colleges with identical acceptance rates can have very different
student bodies.</p>
<h2>What to compare instead</h2>
<p>Look at the admitted-student profile (test score middle 50%, high-school GPA), the graduation
rate, and the net price after aid. A college that admits 70% of applicants but graduates 80% of its
students is usually a better bet than one that admits 30% and graduates 45%. The pages here show all
four numbers side by side so the comparison is possible in one place.</p>
""",
             faq=[("Is a lower acceptance rate better?",
                   "Not necessarily. Acceptance rate measures selectivity only; graduation rate, net "
                   "price and the admitted-student profile say more about the outcome."),
                  ("Does the acceptance rate include transfer students?",
                   "The IPEDS rate covers first-time, degree-seeking freshmen, not transfer applicants."),
                  ("Why is my college's rate different from the website?",
                   "Colleges often quote a rate for a specific term or application cycle; IPEDS uses a "
                   "standard fall cohort so institutions can be compared.")],
             rel=[("Search colleges", "/search/"), ("All states", "/#states")]),

        dict(slug="in-state-vs-out-of-state-tuition",
             title="In-State vs Out-of-State Tuition — How Public College Pricing Works",
             desc="Why public universities charge residents less, what counts as residency, how "
                  "reciprocity programmes work, and why private college sticker prices are the same "
                  "for everyone.",
             h1="In-state vs out-of-state tuition",
             lede="At public universities the price depends on where you live; at private colleges the "
                  "sticker price does not.",
             body="""
<h2>Public universities</h2>
<p>State legislatures subsidise public institutions on the understanding that residents pay less.
In-state students are charged a lower tuition rate; out-of-state and international students pay the
full cost of instruction plus a margin. The gap is large — often two to three times the in-state
price at flagship universities, and it is the single biggest pricing difference in American higher
education.</p>
<h2>Establishing residency</h2>
<p>Residency is defined by state law, not by the university. Typical requirements: twelve months of
physical presence, a state driver's licence, voter registration, tax returns and financial
independence from parents who live elsewhere. Moving to a state mainly to attend college usually
does not qualify, and petitions are audited.</p>
<h2>Reciprocity and waivers</h2>
<p>Many states belong to regional exchange programmes (WICHE in the West, the Midwest Student
Exchange, the Academic Common Market in the South) that let residents of one state pay near-in-state
rates at partner institutions in another. Some universities also offer automatic merit scholarships
that reduce the out-of-state price to roughly the in-state level.</p>
<h2>Private colleges</h2>
<p>Private institutions publish one tuition figure for all students, but almost nobody pays the
sticker price: institutional aid, need-based grants and merit scholarships reduce the net price. That
is why the IPEDS net-price figure for a private college is often half its published tuition — and
why comparing sticker prices across sectors is misleading.</p>
""",
             faq=[("Can I get in-state tuition after one year?",
                   "Only if you meet the state's residency rules — usually a year of physical presence "
                   "plus independence and documentation. Attending college is not by itself enough."),
                  ("Do private colleges charge out-of-state students more?",
                   "No. Private colleges publish the same tuition for everyone; aid packages vary by "
                   "student, not by residence."),
                  ("What is a tuition reciprocity programme?",
                   "A regional agreement that lets residents of one state attend partner institutions "
                   "in another at a reduced, near-in-state rate.")],
             rel=[("Search colleges", "/search/"), ("All states", "/#states")]),

        dict(slug="graduation-rate-explained",
             title="Graduation Rate Explained — What the 150% Cohort Number Means",
             desc="How the federal 150% graduation rate is calculated, who is excluded from the "
                  "cohort, why transfer-out matters, and how to compare colleges fairly.",
             h1="What the graduation rate actually measures",
             lede="The headline rate counts first-time, full-time students who finish within 150% of "
                  "normal time — six years for a bachelor's degree, three for an associate's.",
             body="""
<h2>The cohort</h2>
<p>Each institution tracks the first-time, full-time students who started in a given fall. Students
who transfer in, part-time students and students who started in another term are not in that cohort.
The rate is the share of the cohort who completed a degree or certificate within 150% of the
published programme length.</p>
<h2>Exclusions</h2>
<p>IPEDS allows institutions to exclude a small number of students — those who died, became
permanently disabled, joined the military, or left to serve a religious mission. Those exclusions are
reported separately, so the adjusted cohort used as the denominator is slightly smaller than the raw
cohort.</p>
<h2>Why transfer-out matters</h2>
<p>A student who transfers to another college and graduates there counts as a non-completer for the
first institution. Community colleges and regional universities therefore publish a transfer-out rate
alongside the graduation rate; reading both together gives a fairer picture. A college with a 30%
graduation rate and a 40% transfer-out rate is not losing 70% of its students — many are continuing
elsewhere.</p>
<h2>Comparing fairly</h2>
<p>Compare institutions with similar cohorts and missions. A selective four-year college and an
open-admission community college serve different populations, and their rates are not a like-for-like
quality score. The pages here show the rate, the cohort size and the transfer-out rate together so
the context is visible.</p>
""",
             faq=[("Is 150% graduation rate the same as four-year graduation rate?",
                   "No. It is the share who finish within six years for a bachelor's degree (three "
                   "years for an associate's), not four."),
                  ("Why do community colleges have low graduation rates?",
                   "Many students transfer, study part-time or take a few courses rather than complete "
                   "a credential; the first-time full-time cohort excludes those patterns."),
                  ("Do transfer students count against a college?",
                   "Yes — a student who transfers out counts as a non-completer for the institution "
                   "they left, which is why transfer-out rates are reported too.")],
             rel=[("Search colleges", "/search/"), ("All states", "/#states")]),
    ],

}


def add_guides(site) -> int:
    """Add /guides/ plus one page per guide for this site. Returns the number added."""
    items = GUIDES.get(site.slug, [])
    if not items:
        return 0
    for g in items:
        rel_links = g.get("rel") or [("Search", "/search/")]
        body = (f"<h1>{esc(g['h1'])}</h1><p class=\"lede\">{g['lede']}</p>"
                f"{g['body']}{faq(g['faq'])}{related(rel_links, 'Where to go next')}")
        site.add(f"/guides/{g['slug']}/", g["title"], g["desc"], body,
                 crumbs=[("Guides", "/guides/"), (g["h1"], None)])
    index = ("<h1>Guides</h1><p class=\"lede\">Short, accurate explainers of the systems behind "
             "this directory — written so the data pages make sense.</p>"
             + cards([(f"/guides/{g['slug']}/", esc(g["h1"]), esc(g["desc"][:70]) + "…")
                      for g in items]))
    site.add("/guides/", f"Guides — {site.brand}",
             f"Explainers on {site.brand.lower()}: how the codes work, how to find them and what they "
             f"mean in practice.", index, crumbs=[("Guides", None)])
    return len(items) + 1
