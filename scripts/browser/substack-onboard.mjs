// Substack: full onboarding through publication creation in one continuous session.
import { getBrowser, release } from "./agentbrowser.mjs";

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
const text = async () => (await page.evaluate(() => document.body.innerText || "")).replace(/\s+/g, " ");
const clickBtn = async (re, label) => {
  const ok = await page.getByRole("button", { name: re }).first().click({ timeout: 5000 }).then(() => true).catch(() => false);
  console.log(`${label}: ${ok ? "clicked" : "NOT FOUND"}`);
  await page.waitForTimeout(3500);
  return ok;
};
const fillInputs = async (pairs) => {
  for (const [idx, value] of pairs) {
    const loc = page.locator('input[type="text"], input:not([type])').nth(idx);
    if (await loc.count()) { await loc.fill(value).catch(() => {}); console.log(`filled input ${idx} = ${value}`); }
  }
};

await page.goto("https://substack.com/onboarding?flow=creator_signup", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(4500);

for (let step = 0; step < 14; step++) {
  const t = await text();
  console.log(`\n--- step ${step} ---\n${t.slice(0, 220)}`);
  if (/Select 3 topics/i.test(t)) {
    for (const topic of ["Education", "Technology", "Health & Wellness"]) {
      await page.getByRole("button", { name: topic, exact: true }).first().click({ timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(250);
    }
    await clickBtn(/^continue$/i, "topics continue");
  } else if (/Subscribe to a few Substacks/i.test(t)) {
    await clickBtn(/continue without subscribing|subscribe and continue/i, "skip subs");
  } else if (/Tell us about yourself/i.test(t)) {
    await page.locator('input[name="name"]').first().fill("Tekify Data").catch(() => {});
    await page.locator('input[name="handle"]').first().fill("tekifydata").catch(() => {});
    await page.locator("textarea").first().fill("Open data directories built from public government datasets: IFSC codes, ZIP codes, colleges, hospitals, nursing homes and more.").catch(() => {});
    await page.waitForTimeout(400);
    await clickBtn(/^continue$/i, "profile continue");
  } else if (/Where do you want to start/i.test(t)) {
    await page.getByRole("button", { name: /^create$/i }).first().click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(500);
    await clickBtn(/^continue$/i, "start continue");
  } else if (/(name your publication|publication name|create your publication|publication url|subdomain)/i.test(t)) {
    await fillInputs([[0, "Tekify Open Data"], [1, "tekifyopendata"]]);
    await page.waitForTimeout(800);
    await clickBtn(/^continue$/i, "publication continue");
  } else if (/(start writing|go to dashboard|you.re all set|welcome to substack|publish your first)/i.test(t)) {
    console.log("ONBOARDING COMPLETE");
    break;
  } else {
    console.log("unhandled step; trying next/continue/skip");
    let ok = await clickBtn(/^(next|continue|skip|skip for now|done)$/i, "fallback next");
    if (!ok) {
      const btn = page.locator("button").first();
      if (await btn.count()) { await btn.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(3000); ok = true; }
    }
    if (!ok) break;
  }
}
console.log("\nFINAL URL:", page.url());
await page.screenshot({ path: ".cache/substack_done.png" }).catch(() => {});
await release(h);
process.exit(0);
