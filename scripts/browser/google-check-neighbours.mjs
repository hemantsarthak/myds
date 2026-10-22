// Check whether Google has indexed the OTHER agent's tekify subdomains (pincode/ifsc/solarcalc).
import { getBrowser, release } from "../agentbrowser.mjs";

const QUERIES = ["site:pincode.tekify.xyz", "site:ifsc.tekify.xyz", "site:solarcalc.tekify.xyz", "tekify.xyz"];
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
      const stat = m ? m[0] : null;
      const all = [...document.querySelectorAll("a[href]")].map((a) => a.href);
      const hits = [...new Set(all.filter((u) => u.indexOf("tekify.xyz") >= 0 && u.indexOf("google.com") < 0))].slice(0, 5);
      return { stat: stat, hits: hits };
    });
    console.log(JSON.stringify({ q: q, stat: info.stat, hits: info.hits }));
  } catch (e) {
    console.log(JSON.stringify({ q: q, error: String(e).slice(0, 80) }));
  }
}
await release(h);
process.exit(0);
