// Publish several targeted Telegraph explainer articles, each linking to the relevant directories.
// Telegraph needs no account or captcha; the pages are indexable and give Google discovery paths.
import { getBrowser, release } from "../agentbrowser.mjs";

const ARTICLES = [
  {
    title: "How to find any Indian bank branch's IFSC code (and what it means)",
    blocks: [
      "<p>Every Indian bank branch has an eleven-character IFSC code: four letters for the bank, a zero, and six characters identifying the branch. The code is printed on cheque books and statements, and it is what NEFT, RTGS and IMPS transfers need.</p>",
      "<h3>Look it up in seconds</h3>",
      '<p>The free directory at <a href="https://ifsccodes.tekify.xyz">IFSC Codes India</a> lists every branch with its code, address, MICR number and the transfer systems it supports. You can also search by bank name, city or district. There are 19,511 branch pages, built from the Reserve Bank of India-derived Razorpay IFSC dataset.</p>',
      "<h3>Reading the code</h3>",
      "<p>For example, ABHY0065102: ABHY identifies the bank, 0 is reserved for future use, and 065102 identifies the branch. When you make a transfer you need the IFSC plus the account number — never send money based on a code someone typed into a chat without checking it against the branch record.</p>",
      '<p>More free directories and calculators: <a href="https://tekify.xyz">Tekify</a>.</p>',
    ],
  },
  {
    title: "How CMS star ratings work for hospitals, nursing homes and dialysis centres",
    blocks: [
      "<p>Medicare publishes star ratings for thousands of US healthcare providers, but the measures behind each rating differ by facility type. Here is what each one actually compares.</p>",
      "<h3>Hospitals</h3>",
      '<p>The overall hospital rating combines mortality, safety of care, readmission, patient experience and timely care. Each is compared with what CMS expects for similar patients, then rolled into one to five stars. See every US hospital, with its measure groups and emergency-services flag, at <a href="https://hospitals.tekify.xyz">US Hospitals</a>.</p>',
      "<h3>Nursing homes</h3>",
      '<p>The nursing-home rating adds staffing hours and turnover to health-inspection and quality-measure results. Staffing is often the most useful signal for families. Browse 15,056 facilities at <a href="https://nursinghomes.tekify.xyz">US Nursing Homes</a>.</p>',
      "<h3>Home health agencies</h3>",
      '<p>Home-health ratings focus on how well agencies help patients recover at home, plus patient-experience surveys. See 12,777 agencies at <a href="https://homehealth.tekify.xyz">US Home Health</a>.</p>',
      "<h3>Dialysis facilities</h3>",
      '<p>Dialysis ratings are built from patient survival, hospitalisation, readmission, transfusion and emergency-department visits, plus transplant waitlisting. Browse 7,490 centres at <a href="https://dialysis.tekify.xyz">US Dialysis Centers</a>.</p>',
      '<p>All four directories reproduce official CMS data and state the source on every page. More at <a href="https://tekify.xyz">tekify.xyz</a>.</p>',
    ],
  },
  {
    title: "Free US ZIP code, place, area code and airport data — with JSON indexes",
    blocks: [
      "<p>Reference data is easiest to use when it is both readable by humans and available as JSON. These free directories do both.</p>",
      '<p><a href="https://zipcodes.tekify.xyz">US ZIP Codes</a> — 17,759 ZIP codes with city, county, time zone and neighbouring ZIPs. Each page links to the places and area codes that overlap it.</p>',
      '<p><a href="https://places.tekify.xyz">US Places &amp; Counties</a> — 19,203 places and counties with 2023 Census population estimates, county assignment and the ZIP codes inside each place.</p>',
      '<p><a href="https://areacodes.tekify.xyz">Area Codes</a> — NANP area codes and world dialing codes, searchable by code, city, state or country.</p>',
      '<p><a href="https://airportcodes.tekify.xyz">Airport Codes</a> — 10,181 airports with IATA and ICAO codes, runways, elevation and nearby airports.</p>',
      "<h3>For developers</h3>",
      "<p>Each site serves a compact JSON index under /data/ (for example /data/zips.json) that the search box loads once and filters locally. The datasets come from the US Census Bureau, GeoNames and OurAirports.</p>",
      '<p>Everything is free, no sign-up: <a href="https://tekify.xyz">tekify.xyz</a>.</p>',
    ],
  },
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
const published = [];

for (const art of ARTICLES) {
  await page.goto("https://telegra.ph/", { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForTimeout(2500);
  const markup = `<h3>${art.title}</h3>` + art.blocks.join("");
  await page.evaluate((html) => {
    const ed = document.querySelector(".ql-editor");
    ed.innerHTML = html;
    ed.dispatchEvent(new Event("input", { bubbles: true }));
  }, markup);
  await page.waitForTimeout(1200);
  await page.getByRole("button", { name: /publish/i }).first().click({ timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(3500);
  const url = page.url();
  const title = await page.title();
  published.push({ title: art.title, url, pageTitle: title });
  console.log("published:", url);
  await page.waitForTimeout(1000);
}
console.log(JSON.stringify(published, null, 1));
await release(h);
process.exit(0);
