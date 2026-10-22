// Post one Substack Note per property (each note is a public substack.com page linking to a
// directory — nofollow, but crawlable for discovery and indexable itself).
import { getBrowser, release } from "../agentbrowser.mjs";

const NOTES = [
  ["Indian bank IFSC codes — every branch's code, address, MICR and transfer rails. 19,511 pages:", "https://ifsccodes.tekify.xyz"],
  ["US ZIP codes with city, county, time zone and neighbouring ZIPs. 17,759 pages:", "https://zipcodes.tekify.xyz"],
  ["US places and counties with 2023 population estimates and county assignment. 19,203 pages:", "https://places.tekify.xyz"],
  ["US college data: acceptance rate, in-state/out-of-state tuition, net price by income, graduation rate. 6,056 pages:", "https://colleges.tekify.xyz"],
  ["US hospital directory with CMS star ratings and quality measures. 5,888 pages:", "https://hospitals.tekify.xyz"],
  ["US nursing homes with CMS ratings, staffing hours and turnover. 15,056 pages:", "https://nursinghomes.tekify.xyz"],
  ["US home health agencies with CMS quality ratings and services. 12,777 pages:", "https://homehealth.tekify.xyz"],
  ["Area codes and world dialing codes — lookup by code, city, state or country. 6,954 pages:", "https://areacodes.tekify.xyz"],
  ["Airport codes: IATA/ICAO, runways, elevation and nearby airports. 10,181 pages:", "https://airportcodes.tekify.xyz"],
  ["Free calculators: loans, mortgages, retirement withdrawal, debt payoff, salary, health, dates and units:", "https://calculators.tekify.xyz"],
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
await page.goto("https://substack.com/@tekifydata", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(4000);

for (const [text, url] of NOTES) {
  try {
    await page.getByRole("button", { name: /create a note|what's on your mind/i }).first().click({ timeout: 6000 }).catch(() => {});
    await page.waitForTimeout(2500);
    const editor = page.locator("[contenteditable='true'], textarea").first();
    if (!(await editor.count())) { console.log("no editor for", url); break; }
    await editor.click({ timeout: 5000 }).catch(() => {});
    await page.keyboard.type(text + " " + url, { delay: 6 });
    await page.waitForTimeout(1200);
    const post = page.getByRole("button", { name: /^(post|publish|send)$/i }).first();
    if (await post.count()) {
      await post.click({ timeout: 8000 }).catch(() => {});
      await page.waitForTimeout(4500);
      console.log("posted note ->", url);
    } else {
      console.log("no post button for", url);
      break;
    }
    await page.goto("https://substack.com/@tekifydata", { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(2500);
  } catch (e) {
    console.log("note failed for", url, String(e).slice(0, 100));
  }
}

const count = await page.evaluate(() => [...document.querySelectorAll("a[href*='tekify.xyz']")].length);
console.log("tekify links visible on profile:", count);
await page.screenshot({ path: ".cache/substack_notes.png" }).catch(() => {});
await release(h);
process.exit(0);
