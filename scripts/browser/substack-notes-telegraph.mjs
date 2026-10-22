// Post Substack notes that link to the Telegraph explainers (chain: substack -> telegra.ph -> sites).
import { getBrowser, release } from "../agentbrowser.mjs";

const NOTES = [
  ["New explainer: how to check a US hospital's CMS star rating before scheduling care (and what the rating does not tell you). ", "https://telegra.ph/How-to-check-a-US-hospital-CMS-star-rating-before-scheduling-care-10-22"],
  ["New explainer: what the CMS nursing-home star rating does and does not tell you, including staffing hours and turnover. ", "https://telegra.ph/Choosing-a-nursing-home-what-the-CMS-star-rating-does-and-does-not-tell-you-10-22"],
  ["New explainer: what the five digits of a US ZIP code mean, and how to look one up with its city, county and neighbours. ", "https://telegra.ph/US-ZIP-codes-what-the-five-digits-mean-and-how-to-look-one-up-10-22"],
  ["New explainer: IATA vs ICAO airport codes, why both exist, and how to look up runways, elevation and nearby airports. ", "https://telegra.ph/IATA-vs-ICAO-airport-codes-the-difference-and-where-to-look-them-up-10-22"],
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
let posted = 0;
for (const pair of NOTES) {
  const text = pair[0];
  const url = pair[1];
  try {
    await page.goto("https://substack.com/@tekifydata", { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(3200);
    await page.getByText(/what's on your mind\?/i).first().click({ timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(4200);
    const editor = page.locator('[role="dialog"] [contenteditable="true"], [contenteditable="true"]').last();
    if (!(await editor.count())) { console.log("no editor"); continue; }
    await editor.click({ timeout: 5000 }).catch(() => {});
    await page.keyboard.type(text + url, { delay: 4 });
    await page.waitForTimeout(2200);
    const post = page.getByRole("button", { name: /^post$/i }).last();
    if (await post.count()) {
      await post.click({ timeout: 8000 }).catch(() => {});
      await page.waitForTimeout(4500);
      posted++;
      console.log("posted note:", url);
    }
  } catch (e) {
    console.log("note failed:", String(e).slice(0, 80));
  }
}
console.log("notes posted:", posted);
await release(h);
process.exit(0);
