// Substack: retry profile save (bio + website) and post a Note with a link to tekify.xyz.
import { getBrowser, release } from "../agentbrowser.mjs";

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());

// --- profile edit with explicit save + verification
await page.goto("https://substack.com/profile/edit", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(4500);
const bioSel = 'textarea[name="profile-bio"], [name="profile-bio"]';
await page.locator(bioSel).first().fill("Open data directories built from public government datasets: IFSC codes, ZIP codes, US colleges, hospitals, nursing homes, home health, area codes, airports. https://tekify.xyz").catch(() => {});
const webOk = await page.evaluate(() => {
  const labels = [...document.querySelectorAll("*")].filter((el) => el.children.length === 0 && /^Website$/i.test((el.textContent || "").trim()));
  if (!labels.length) return "no-website-label";
  let node = labels[0];
  for (let i = 0; i < 6 && node; i++) {
    node = node.parentElement;
    const inp = node && node.querySelector("input[type='text']");
    if (inp) {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
      setter.call(inp, "https://tekify.xyz");
      inp.dispatchEvent(new Event("input", { bubbles: true }));
      inp.dispatchEvent(new Event("change", { bubbles: true }));
      inp.blur();
      return "ok";
    }
  }
  return "no-input";
});
console.log("website:", webOk);
await page.waitForTimeout(800);
const done = page.getByRole("button", { name: /^done$/i }).first();
if (await done.count()) { await done.click({ timeout: 8000 }).catch(() => {}); }
await page.waitForTimeout(5000);
await page.goto("https://substack.com/@tekifydata", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(4000);
const saved = await page.evaluate(() => ({
  text: (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 350),
  tekifyLinks: [...document.querySelectorAll("a[href*='tekify']")].map((a) => a.href).slice(0, 5),
}));
console.log("profile now:", JSON.stringify(saved, null, 1));

// --- post a Note
await page.getByRole("button", { name: /create a note/i }).first().click({ timeout: 6000 }).catch(() => {});
await page.waitForTimeout(3000);
const editor = page.locator("[contenteditable='true'], textarea").first();
if (await editor.count()) {
  await editor.click({ timeout: 5000 }).catch(() => {});
  await page.keyboard.type("Open data directories from public government datasets — Indian IFSC bank codes, US ZIP codes, places and counties, colleges, hospitals, nursing homes, home health, area codes and airport codes. All free, no signup: https://tekify.xyz", { delay: 8 });
  await page.waitForTimeout(1500);
  const post = page.getByRole("button", { name: /^(post|publish|send)$/i }).first();
  if (await post.count()) { await post.click({ timeout: 8000 }).catch(() => {}); }
  await page.waitForTimeout(5000);
  const noteState = await page.evaluate(() => ({
    url: location.href,
    text: (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 300),
    tekifyLinks: [...document.querySelectorAll("a[href*='tekify']")].map((a) => a.href).slice(0, 5),
  }));
  console.log("note:", JSON.stringify(noteState, null, 1));
} else {
  console.log("no note editor found");
}
await page.screenshot({ path: ".cache/substack_note.png" }).catch(() => {});
await release(h);
process.exit(0);
