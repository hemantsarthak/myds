// Try a Medium account with medium@tekify.xyz (email signup, then read the magic link from our
// inbox). If the account works, publish an explainer article linking to the directories.
import { getBrowser, release } from "../agentbrowser.mjs";

const EMAIL = "medium@tekify.xyz";
const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());

await page.goto("https://medium.com/m/signin", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(3500);
const info = await page.evaluate(() => ({
  url: location.href,
  text: (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 300),
  inputs: [...document.querySelectorAll("input")].map((i) => ({ type: i.type, name: i.name || i.id, ph: i.placeholder || "" })).filter((i) => i.type !== "hidden").slice(0, 8),
  buttons: [...document.querySelectorAll("button")].map((b) => (b.innerText || "").trim()).filter(Boolean).slice(0, 10),
}));
console.log("landing:", JSON.stringify(info, null, 1));

// try the email input
const emailInput = page.locator('input[type="email"], input[name="email"]').first();
if (await emailInput.count()) {
  await emailInput.fill(EMAIL);
  await page.waitForTimeout(600);
  await page.getByRole("button", { name: /continue|next|sign/i }).first().click({ timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(6000);
  const after = await page.evaluate(() => ({
    url: location.href,
    text: (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 400),
  }));
  console.log("after email:", JSON.stringify(after, null, 1));
}
await page.screenshot({ path: ".cache/medium.png" }).catch(() => {});
await release(h);
process.exit(0);
