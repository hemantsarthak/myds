// Verify the four new calculators recompute live in a real browser (#calcout).
import { getBrowser, release } from "../agentbrowser.mjs";

const CASES = [
  ["net-worth-calculator", "debts", "300000"],
  ["stock-profit-calculator", "shares", "250"],
  ["crypto-profit-calculator", "sell", "60000"],
  ["emergency-fund-calculator", "months", "9"],
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
const errors = [];
page.on("pageerror", (e) => errors.push(String(e).slice(0, 100)));
for (const pair of CASES) {
  const slug = pair[0];
  const field = pair[1];
  const value = pair[2];
  try {
    await page.goto("https://calculators.tekify.xyz/" + slug + "/", { waitUntil: "domcontentloaded", timeout: 40000 });
    await page.waitForTimeout(1400);
    const read = () => page.evaluate(() => {
      const el = document.querySelector("#calcout");
      return el ? el.innerText.replace(/\s+/g, " ").slice(0, 150) : "(no #calcout)";
    });
    const before = await read();
    const input = page.locator('input[name="' + field + '"]').first();
    if (!(await input.count())) { console.log(slug, "NO INPUT", field); continue; }
    await input.fill(value);
    await page.waitForTimeout(900);
    const after = await read();
    console.log(slug, "\n  before:", before, "\n  after :", after, "\n  changed:", before !== after);
  } catch (e) {
    console.log(slug, "ERR", String(e).slice(0, 80));
  }
}
console.log("page errors:", errors.slice(0, 5));
await release(h);
process.exit(0);
