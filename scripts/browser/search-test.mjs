// Functional test: every site's search box must actually produce results, and a calculator page
// must recompute when inputs change.
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
  ["areacodes", "212"],
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
const results = [];
const errors = [];
page.on("pageerror", (e) => errors.push(String(e).slice(0, 120)));

for (const [site, q] of CASES) {
  for (const path of ["/", "/search/"]) {
    const url = `https://${site}.tekify.xyz${path}`;
    try {
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 40000 });
      await page.waitForTimeout(1200);
      const input = page.locator("#q").first();
      if (!(await input.count())) { results.push([site, path, "NO #q INPUT"]); continue; }
      await input.click();
      await input.type(q, { delay: 15 });
      await page.waitForTimeout(2200);
      const info = await page.evaluate(() => {
        const res = document.querySelector("#res");
        const links = res ? res.querySelectorAll("a").length : -1;
        return { links, text: res ? (res.innerText || "").replace(/\s+/g, " ").slice(0, 80) : "(no #res)" };
      });
      results.push([site, path, info.links > 0 ? `OK (${info.links} links)` : `FAIL ${info.text}`]);
    } catch (e) {
      results.push([site, path, "ERR " + String(e).slice(0, 80)]);
    }
  }
}

// calculators: home filter + a live calculation
try {
  await page.goto("https://calculators.tekify.xyz/", { waitUntil: "domcontentloaded", timeout: 40000 });
  await page.waitForTimeout(1500);
  await page.locator("#q").first().type("mortgage", { delay: 20 });
  await page.waitForTimeout(1200);
  const visible = await page.evaluate(() => [...document.querySelectorAll("#tools a")].filter((a) => a.style.display !== "none").length);
  results.push(["calculators", "/", visible > 0 && visible < 67 ? `OK (filter -> ${visible})` : `FAIL (visible=${visible})`]);

  await page.goto("https://calculators.tekify.xyz/mortgage-payment/", { waitUntil: "domcontentloaded", timeout: 40000 });
  await page.waitForTimeout(1500);
  const before = await page.evaluate(() => (document.querySelector("[data-out], .result, output") || {}).innerText || document.body.innerText.slice(0, 0));
  const amount = page.locator('input[type="number"]').first();
  if (await amount.count()) {
    await amount.fill("400000");
    await amount.dispatchEvent("input");
    await page.waitForTimeout(1500);
  }
  const out = await page.evaluate(() => {
    const el = document.querySelector("[data-out], .result, output");
    return el ? el.innerText.slice(0, 60) : document.body.innerText.match(/1,?4[0-9]{2}[.,][0-9]{2}/) ? "found payment" : "no result element";
  });
  results.push(["calculators", "/mortgage-payment/", `live output: ${String(out).slice(0, 60)}`]);
} catch (e) {
  results.push(["calculators", "-", "ERR " + String(e).slice(0, 80)]);
}

console.log("RESULTS");
for (const r of results) console.log(`  ${r[0].padEnd(14)} ${r[1].padEnd(22)} ${r[2]}`);
console.log("page errors:", errors.slice(0, 10));
await release(h);
process.exit(0);
