// Check whether Google has indexed the GitHub Pages site (github.io is crawled heavily).
import { getBrowser, release } from "../agentbrowser.mjs";

const QUERIES = ["site:hemantsarthak.github.io", "site:github.io tekify", "hemantsarthak.github.io myds"];
const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
for (const q of QUERIES) {
  try {
    await page.goto("https://www.google.com/search?hl=en&num=20&q=" + encodeURIComponent(q),
                    { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(2200);
    const info = await page.evaluate(() => {
      const t = document.body ? document.body.innerText : "";
      const m = t.match(/(About [\d,]+ results|[\d,]+ results|did not match any documents)/i);
      const anchors = Array.from(document.querySelectorAll("a[href]")).map((a) => a.href);
      const filtered = anchors.filter((u) => u.indexOf("github.io") >= 0 && u.indexOf("google.com") < 0);
      const ours = Array.from(new Set(filtered));
      return { stat: m ? m[0] : null, ours: ours.slice(0, 4) };
    });
    console.log(JSON.stringify({ q: q, ...info }));
  } catch (e) {
    console.log(JSON.stringify({ q: q, error: String(e).slice(0, 80) }));
  }
}
await release(h);
process.exit(0);
