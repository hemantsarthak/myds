// Substack: create the publication (claim URL + name/description) in one continuous flow.
import { getBrowser, release } from "../agentbrowser.mjs";

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
const text = async () => (await page.evaluate(() => document.body.innerText || "")).replace(/\s+/g, " ");
const clickBtn = async (re, label) => {
  const ok = await page.getByRole("button", { name: re }).first().click({ timeout: 6000 }).then(() => true).catch(() => false);
  console.log(`${label}: ${ok ? "clicked" : "NOT FOUND"}`);
  await page.waitForTimeout(3500);
  return ok;
};

await page.goto("https://substack.com/settings", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(4000);
await page.getByRole("button", { name: /start a substack/i }).first().click({ timeout: 8000 }).catch(() => {});
await page.waitForTimeout(6000);

// step: claim URL
const sub = page.locator('input[name="subdomain"]').first();
if (await sub.count()) {
  await sub.fill("tekifyopendata");
  console.log("filled subdomain");
  await page.waitForTimeout(800);
  await clickBtn(/^continue$/i, "url continue");
}

for (let step = 0; step < 10; step++) {
  const t = await text();
  console.log(`\n--- step ${step} @ ${page.url()} ---\n${t.slice(0, 240)}`);
  if (/available|not available|taken/i.test(t) && /subdomain|url/i.test(t)) {
    console.log("URL availability message; trying another subdomain");
    await page.locator('input[name="subdomain"]').first().fill("tekifydata").catch(() => {});
    await page.waitForTimeout(600);
    await clickBtn(/^continue$/i, "url retry");
    continue;
  }
  if (/(name your publication|publication name|what.s your publication called|title)/i.test(t)) {
    const inp = page.locator('input[type="text"], input:not([type])').first();
    if (await inp.count()) { await inp.fill("Tekify Open Data").catch(() => {}); }
    await clickBtn(/^continue$/i, "name continue");
  } else if (/(description|about your publication|bio)/i.test(t) && /(publication|substack)/i.test(t)) {
    const ta = page.locator("textarea").first();
    if (await ta.count()) await ta.fill("Open data directories built from public government datasets: IFSC bank codes, ZIP codes, US places, colleges, hospitals, nursing homes, home health, area codes and airport codes.").catch(() => {});
    await clickBtn(/^continue$/i, "desc continue");
  } else if (/(start writing|go to dashboard|you.re all set|welcome|publish your first|create your first)/i.test(t)) {
    console.log("PUBLICATION READY");
    break;
  } else if (/(skip|not now|maybe later)/i.test(t)) {
    await clickBtn(/skip|not now|maybe later/i, "skip step");
  } else if (await clickBtn(/^continue$/i, "generic continue")) {
    // continue
  } else if (await clickBtn(/^next$/i, "generic next")) {
    // next
  } else {
    console.log("no actionable button; stopping");
    break;
  }
}
console.log("\nFINAL URL:", page.url());
await page.screenshot({ path: ".cache/substack_pub_done.png" }).catch(() => {});
await release(h);
process.exit(0);
