// Re-test home-page search with a longer wait (cold-cache JSON fetches are ~0.5-1.5 MB).
import { getBrowser, release } from "../agentbrowser.mjs";

const CASES = [
  ["ifsccodes", "HDFC"],
  ["airportcodes", "Heathrow"],
  ["zipcodes", "90210"],
  ["places", "Austin"],
  ["colleges", "Harvard"],
  ["hospitals", "Johns Hopkins"],
  ["nursinghomes", "Sunrise"],
  ["homehealth", "Providence"],
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
const errors = [];
page.on("pageerror", (e) => errors.push(String(e).slice(0, 140)));
const out = [];
for (const [site, q] of CASES) {
  try {
    await page.goto(`https://${site}.tekify.xyz/`, { waitUntil: "domcontentloaded", timeout: 40000 });
    await page.waitForTimeout(1500);
    const input = page.locator("#q").first();
    await input.click();
    await page.waitForTimeout(4000); // let the index fetch finish on first focus
    await input.type(q, { delay: 20 });
    await page.waitForTimeout(4000);
    const info = await page.evaluate(() => {
      const res = document.querySelector("#res");
      return { links: res ? res.querySelectorAll("a").length : -1, text: res ? (res.innerText || "").replace(/\s+/g, " ").slice(0, 70) : "no #res" };
    });
    out.push([site, info.links > 0 ? `OK (${info.links} links)` : `FAIL ${info.text}`]);
  } catch (e) {
    out.push([site, "ERR " + String(e).slice(0, 80)]);
  }
}
for (const [s, r] of out) console.log(`  ${s.padEnd(14)} ${r}`);
console.log("page errors:", errors.slice(0, 8));
await release(h);
process.exit(0);
