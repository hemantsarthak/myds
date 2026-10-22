// Check whether Google has discovered/indexed anything new: our domain, and whether it has indexed
// the Substack notes that link to us.
import { getBrowser, release } from "../agentbrowser.mjs";

const QUERIES = [
  "site:tekify.xyz",
  "site:ifsccodes.tekify.xyz",
  "site:substack.com tekifydata",
  "tekify.xyz",
];
const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
for (const q of QUERIES) {
  try {
    await page.goto("https://www.google.com/search?hl=en&num=20&q=" + encodeURIComponent(q),
                    { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(2200);
    const info = await page.evaluate(() => {
      const t = document.body ? document.body.innerText : "";
      const stat = (t.match(/(About [\d,]+ results|[\d,]+ results|did not match any documents)/i) || [null])[0];
      const ours = [...new Set([...document.querySelectorAll("a[href]")].map((a) => a.href).filter((u) => /tekify\.xyz/.test(u)))];
      const substack = [...new Set([...document.querySelectorAll("a[href]")].map((a) => a.href).filter((u) => /substack\.com/.test(u)))].slice(0, 3);
      return { stat, ours: ours.slice(0, 5), substack };
    });
    console.log(JSON.stringify({ q, ...info }));
  } catch (e) {
    console.log(JSON.stringify({ q, error: String(e).slice(0, 100) }));
  }
}
await release(h);
process.exit(0);
