// Substack: set the profile bio + Website link to tekify.xyz, save, then post a Note.
import { getBrowser, release } from "../agentbrowser.mjs";

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());

await page.goto("https://substack.com/profile/edit", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(4000);

// bio
const bio = page.locator('textarea[name="profile-bio"], [name="profile-bio"]').first();
if (await bio.count()) {
  await bio.fill("Open data directories built from public government datasets: IFSC bank codes, ZIP codes, US places and counties, colleges, hospitals, nursing homes, home health, area codes and airport codes. https://tekify.xyz");
  console.log("bio set");
}
// website field: find the input that follows the "Website" label
const webOk = await page.evaluate(() => {
  const labels = [...document.querySelectorAll("*")].filter((el) => el.children.length === 0 && /^Website$/i.test((el.textContent || "").trim()));
  if (!labels.length) return false;
  let node = labels[0];
  for (let i = 0; i < 6 && node; i++) {
    node = node.parentElement;
    const inp = node && node.querySelector("input[type='text']");
    if (inp) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
      setter.call(inp, "https://tekify.xyz");
      inp.dispatchEvent(new Event("input", { bubbles: true }));
      inp.dispatchEvent(new Event("change", { bubbles: true }));
      return true;
    }
  }
  return false;
});
console.log("website set:", webOk);
await page.waitForTimeout(500);
await page.getByRole("button", { name: /^done$/i }).first().click({ timeout: 8000 }).catch((e) => console.log("done click:", String(e).slice(0, 100)));
await page.waitForTimeout(5000);
const after = await page.evaluate(() => ({
  url: location.href,
  text: (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 400),
  links: [...document.querySelectorAll("a[href*='tekify']")].map((a) => a.href).slice(0, 5),
}));
console.log("after save:", JSON.stringify(after, null, 1));
await page.screenshot({ path: ".cache/substack_profile_saved.png" }).catch(() => {});
await release(h);
process.exit(0);
