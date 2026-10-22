// Post one Substack Note per property: click the prompt, type in the "New note" composer, Post.
import { getBrowser, release } from "../agentbrowser.mjs";

const NOTES = [
  ["Indian bank IFSC codes — every branch's code, address, MICR and transfer rails. 19,511 pages:", "https://ifsccodes.tekify.xyz"],
  ["US ZIP codes with city, county, time zone and neighbouring ZIPs. 17,759 pages:", "https://zipcodes.tekify.xyz"],
  ["US places and counties with 2023 population estimates and county assignment. 19,203 pages:", "https://places.tekify.xyz"],
  ["US college data: acceptance rate, tuition, net price by income, graduation rate. 6,056 pages:", "https://colleges.tekify.xyz"],
  ["US hospital directory with CMS star ratings and quality measures. 5,888 pages:", "https://hospitals.tekify.xyz"],
  ["US nursing homes with CMS ratings, staffing hours and turnover. 15,056 pages:", "https://nursinghomes.tekify.xyz"],
  ["US home health agencies with CMS quality ratings and services. 12,777 pages:", "https://homehealth.tekify.xyz"],
  ["Area codes and world dialing codes — lookup by code, city, state or country. 6,954 pages:", "https://areacodes.tekify.xyz"],
  ["Airport codes: IATA and ICAO codes, runways, elevation and nearby airports. 10,181 pages:", "https://airportcodes.tekify.xyz"],
  ["Free calculators: loans, mortgages, retirement withdrawal, debt payoff, salary, health, dates and units:", "https://calculators.tekify.xyz"],
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
let posted = 0;

for (const [text, url] of NOTES) {
  try {
    await page.goto("https://substack.com/@tekifydata", { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(3500);
    await page.getByText(/what's on your mind\?/i).first().click({ timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(4500);
    const editor = page.locator('[role="dialog"] [contenteditable="true"], [contenteditable="true"]').last();
    if (!(await editor.count())) { console.log("no editor:", url); continue; }
    await editor.click({ timeout: 5000 }).catch(() => {});
    await page.keyboard.type(text + " " + url, { delay: 5 });
    await page.waitForTimeout(2500);
    const post = page.getByRole("button", { name: /^post$/i }).last();
    if (!(await post.count())) { console.log("no Post button:", url); continue; }
    await post.click({ timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(5000);
    posted++;
    console.log("posted:", url);
  } catch (e) {
    console.log("failed:", url, String(e).slice(0, 90));
  }
}
console.log("notes posted this run:", posted, "/", NOTES.length);
await page.goto("https://substack.com/@tekifydata", { waitUntil: "domcontentloaded", timeout: 45000 }).catch(() => {});
await page.waitForTimeout(3000);
const links = await page.evaluate(() => [...document.querySelectorAll("a[href*='tekify.xyz']")].map((a) => a.href));
console.log("tekify links on profile:", links.length);
await release(h);
process.exit(0);
