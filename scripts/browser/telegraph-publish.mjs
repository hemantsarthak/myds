// Publish a Telegraph page through the web editor: inject HTML into the Quill editor, click PUBLISH,
// handle the author dialog, and report the resulting URL.
import { getBrowser, release } from "../agentbrowser.mjs";

const SITES = [
  ["Tekify", "https://tekify.xyz", "Network homepage — free data directories and calculators"],
  ["IFSC Codes India", "https://ifsccodes.tekify.xyz", "Every Indian bank branch's IFSC code, address, MICR and transfer rails (19,511 pages)"],
  ["US ZIP Codes", "https://zipcodes.tekify.xyz", "US ZIP codes with city, county, time zone and neighbouring ZIPs (17,759 pages)"],
  ["US Places & Counties", "https://places.tekify.xyz", "US places and counties with 2023 population estimates and county assignment (19,203 pages)"],
  ["US Colleges", "https://colleges.tekify.xyz", "Acceptance rates, tuition, net price by income and graduation rates (6,056 pages)"],
  ["US Hospitals", "https://hospitals.tekify.xyz", "CMS hospital star ratings and quality measures (5,888 pages)"],
  ["US Nursing Homes", "https://nursinghomes.tekify.xyz", "CMS nursing-home ratings, staffing hours and turnover (15,056 pages)"],
  ["US Home Health", "https://homehealth.tekify.xyz", "CMS home-health agency ratings and services (12,777 pages)"],
  ["US Dialysis Centers", "https://dialysis.tekify.xyz", "CMS dialysis facility five-star ratings and quality measures (7,809 pages)"],
  ["Area Codes", "https://areacodes.tekify.xyz", "NANP area codes and world dialing codes by code, city or state (6,954 pages)"],
  ["Airport Codes", "https://airportcodes.tekify.xyz", "IATA/ICAO airport codes, runways and nearby airports (10,181 pages)"],
  ["Calculators", "https://calculators.tekify.xyz", "Free loan, mortgage, retirement, salary, health and date calculators (67 pages)"],
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
await page.goto("https://telegra.ph/", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(3000);

const html = [
  "<h3>Open data directories: IFSC codes, ZIP codes, colleges, hospitals, nursing homes and more</h3>",
  "<p>Free, ad-light reference directories built from open government and public datasets. One page per record, plus plain JSON indexes for programmatic use.</p>",
  "<h3>Directories</h3>",
  ...SITES.map(([name, url, desc]) => `<p><a href="${url}">${name}</a> — ${desc}</p>`),
  "<h3>What these are</h3>",
  "<p>Each directory turns a public dataset into a readable page per record: Indian bank branch IFSC codes, US ZIP codes, US places and counties, college admissions and net price, CMS hospital / nursing-home / home-health / dialysis quality ratings, area codes and airport codes. Every site also serves a JSON index for developers.</p>",
  "<p>Sources: US Census Bureau, CMS, NCES/IPEDS, GeoNames, OurAirports, Razorpay IFSC (MIT), and others — each site states its source and licence.</p>",
].join("");

await page.evaluate((markup) => {
  const ed = document.querySelector(".ql-editor");
  ed.innerHTML = markup;
  ed.dispatchEvent(new Event("input", { bubbles: true }));
}, html);
await page.waitForTimeout(1500);

// click PUBLISH
await page.getByRole("button", { name: /publish/i }).first().click({ timeout: 8000 }).catch((e) => console.log("publish click:", String(e).slice(0, 100)));
await page.waitForTimeout(4000);

// author dialog?
const dialog = await page.evaluate(() => ({
  url: location.href,
  text: (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 400),
  inputs: [...document.querySelectorAll("input")].map((i) => ({ type: i.type, name: i.name || i.id, ph: i.placeholder || "" })).filter((i) => i.type !== "hidden"),
  buttons: [...document.querySelectorAll("button")].map((b) => (b.innerText || "").trim()).filter(Boolean).slice(0, 10),
}));
console.log("after publish:", JSON.stringify(dialog, null, 1));

// fill author if asked and confirm
const authorInput = page.locator('input[placeholder*="name" i], input[name*="author" i]').first();
if (await authorInput.count()) {
  await authorInput.fill("Tekify");
  await page.waitForTimeout(500);
  await page.getByRole("button", { name: /publish|create|ok/i }).first().click({ timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(5000);
}
const final = await page.evaluate(() => ({ url: location.href, title: document.title }));
console.log("final:", JSON.stringify(final));
if (final.url.includes("telegra.ph")) {
  const links = await page.evaluate(() => [...document.querySelectorAll("a[href*='tekify.xyz']")].map((a) => ({ href: a.href, rel: a.getAttribute("rel") || "(none)" })));
  console.log("links:", JSON.stringify(links.slice(0, 4), null, 1));
}
await page.screenshot({ path: ".cache/telegraph_publish.png" }).catch(() => {});
await release(h);
process.exit(0);
