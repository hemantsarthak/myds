// Substack: full creator onboarding + publication creation, driven by step detection.
import { getBrowser, release } from "./agentbrowser.mjs";

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
const text = async () => (await page.evaluate(() => document.body.innerText || "")).replace(/\s+/g, " ");
const clickBtn = async (re, label) => {
  const ok = await page.getByRole("button", { name: re }).first().click({ timeout: 6000 }).then(() => true).catch(() => false);
  console.log(`${label}: ${ok ? "clicked" : "not found"}`);
  await page.waitForTimeout(4000);
  return ok;
};
const fill = async (sel, value) => {
  const loc = page.locator(sel).first();
  if (await loc.count()) { await loc.fill(value).catch(() => {}); return true; }
  return false;
};

await page.goto("https://substack.com/onboarding?flow=creator_signup", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(4500);

for (let step = 0; step < 10; step++) {
  const t = await text();
  console.log(`\n--- step ${step} @ ${page.url()} ---\n${t.slice(0, 180)}`);

  if (/Select 3 topics/i.test(t)) {
    for (const topic of ["Education", "Technology", "Health & Wellness"]) {
      await page.getByRole("button", { name: topic, exact: true }).first().click({ timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(300);
    }
    await clickBtn(/^continue$/i, "topics continue");
  } else if (/Subscribe to a few Substacks/i.test(t)) {
    await clickBtn(/continue without subscribing|subscribe and continue/i, "skip subscriptions");
  } else if (/Tell us about yourself/i.test(t)) {
    await fill('input[name="name"]', "Tekify Data");
    await fill('input[name="handle"]', "tekifydata");
    await fill("textarea", "Open data directories built from public government datasets: IFSC codes, ZIP codes, colleges, hospitals, nursing homes and more.");
    await page.waitForTimeout(500);
    await clickBtn(/^continue$/i, "profile continue");
  } else if (/publication/i.test(t) && /(name|create|start)/i.test(t)) {
    console.log("PUBLICATION STEP REACHED");
    await page.screenshot({ path: ".cache/substack_publication.png" }).catch(() => {});
    break;
  } else {
    console.log("unknown step; stopping");
    await page.screenshot({ path: ".cache/substack_unknown.png" }).catch(() => {});
    break;
  }
}
console.log("\nfinal url:", page.url());
await release(h);
process.exit(0);
