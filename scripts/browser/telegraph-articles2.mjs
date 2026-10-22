// Publish more targeted Telegraph explainers (no account/captcha), each linking relevant directories.
import { getBrowser, release } from "../agentbrowser.mjs";

const ARTICLES = [
  {
    title: "How to check a US hospital CMS star rating before scheduling care",
    blocks: [
      "<p>Medicare Care Compare gives every hospital an overall star rating from one to five, built from five measure groups: mortality, safety of care, readmission, patient experience and timely care. Here is how to read it without over-reading it.</p>",
      "<h3>Start with the overall rating, then open the groups</h3>",
      "<p>A hospital can be strong on survival and weak on readmission. The overall rating hides that trade-off, so open the individual groups. Each measure is compared with what CMS expects for hospitals treating similar patients.</p>",
      "<p>Every US hospital, with its measure groups, emergency-services flag and address, is listed at <a href=\"https://hospitals.tekify.xyz\">US Hospitals</a>, 5,888 pages, free.</p>",
      "<h3>Three things the rating will not tell you</h3>",
      "<p>It does not measure whether your specific surgeon or procedure is good at that hospital, it does not capture emergency-department wait times, and hospitals with too few cases may be unrated. Treat it as one input alongside a doctor referral and your insurance network.</p>",
      "<p>Related directories: <a href=\"https://nursinghomes.tekify.xyz\">nursing homes</a>, <a href=\"https://homehealth.tekify.xyz\">home health agencies</a>, <a href=\"https://dialysis.tekify.xyz\">dialysis centres</a>. More at <a href=\"https://tekify.xyz\">tekify.xyz</a>.</p>"
    ]
  },
  {
    title: "Choosing a nursing home: what the CMS star rating does and does not tell you",
    blocks: [
      "<p>CMS rates nursing homes on three dimensions, health inspections, staffing and quality measures, plus an overall rating. For families, staffing is often the most informative of the four.</p>",
      "<h3>Staffing hours and turnover</h3>",
      "<p>The staffing measures report nurse hours per resident per day and how often staff turn over. High turnover is a warning sign: consistent carers matter more than a brochure. Both figures appear on every facility page in the free directory at <a href=\"https://nursinghomes.tekify.xyz\">US Nursing Homes</a>.</p>",
      "<h3>What the star rating does not capture</h3>",
      "<p>It does not measure food, activities, the atmosphere of the building or whether the home takes your family member insurance. Those need a visit and questions. Use the rating to build a shortlist, not to make the decision.</p>",
      "<p>15,056 facilities with ratings, ownership and staffing at <a href=\"https://nursinghomes.tekify.xyz\">nursinghomes.tekify.xyz</a>. Related: <a href=\"https://homehealth.tekify.xyz\">home health agencies</a>.</p>"
    ]
  },
  {
    title: "US ZIP codes: what the five digits mean and how to look one up",
    blocks: [
      "<p>A US ZIP code is five digits: the first digit identifies a group of states, the next two a sectional centre facility, and the last two a delivery area. ZIP+4 adds four digits for a specific block or building.</p>",
      "<h3>What a ZIP code is not</h3>",
      "<p>ZIP codes are postal delivery routes, not legal boundaries. They do not map cleanly to cities or counties: one ZIP can span several counties, and a city can contain many ZIPs. That is why address databases and census tools disagree, they are reconciling two different geographies.</p>",
      "<p>The free directory at <a href=\"https://zipcodes.tekify.xyz\">US ZIP Codes</a> shows each ZIP primary city, county, time zone and neighbouring ZIPs, and links to the places and area codes that overlap it.</p>",
      "<h3>For developers</h3>",
      "<p>A compact JSON index is served at /data/zips.json, built from US Census and GeoNames data, so you can resolve a ZIP to a city, county and coordinates without an API key.</p>",
      "<p>Related: <a href=\"https://places.tekify.xyz\">places and counties</a>, <a href=\"https://areacodes.tekify.xyz\">area codes</a>.</p>"
    ]
  },
  {
    title: "IATA vs ICAO airport codes: the difference and where to look them up",
    blocks: [
      "<p>Airports usually have two codes: a three-letter IATA code used by airlines and passengers (LHR, JFK) and a four-letter ICAO code used by air-traffic control (EGLL, KJFK).</p>",
      "<h3>How they are built</h3>",
      "<p>IATA codes are assigned for commercial branding and are not systematic. ICAO codes are regional: the first letter identifies the region (K for the contiguous US, E for northern Europe), followed by a country and airport identifier.</p>",
      "<p>Look up either code, plus runways, elevation and the nearest airports, at <a href=\"https://airportcodes.tekify.xyz\">Airport Codes</a>, 10,181 airports from the OurAirports public dataset.</p>",
      "<h3>Why nearby airports matter</h3>",
      "<p>Cheap fares often involve a secondary airport an hour away. Each airport page lists the nearest airports with distances, so you can see the trade-off before booking.</p>",
      "<p>More at <a href=\"https://tekify.xyz\">tekify.xyz</a>.</p>"
    ]
  }
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
const published = [];
for (const art of ARTICLES) {
  try {
    await page.goto("https://telegra.ph/", { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(2300);
    const markup = "<h3>" + art.title + "</h3>" + art.blocks.join("");
    await page.evaluate((html) => {
      const ed = document.querySelector(".ql-editor");
      ed.innerHTML = html;
      ed.dispatchEvent(new Event("input", { bubbles: true }));
    }, markup);
    await page.waitForTimeout(1000);
    await page.getByRole("button", { name: /publish/i }).first().click({ timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(3200);
    published.push({ title: art.title, url: page.url() });
    console.log("published:", page.url());
  } catch (e) {
    console.log("failed:", art.title, String(e).slice(0, 90));
  }
}
console.log(JSON.stringify(published, null, 1));
await release(h);
process.exit(0);
