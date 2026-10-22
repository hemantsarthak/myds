// Check whether Google has indexed our external publications (Telegraph articles, Substack profile)
// and whether DuckDuckGo/Bing surface our own pages for real content queries.
import { getBrowser, release } from "../agentbrowser.mjs";

const GOOGLE = [
  "site:telegra.ph Tekify",
  "site:substack.com tekifydata",
  "site:github.com hemantsarthak myds",
];
const DDG = [
  "Edgerton Hospital CMS rating",
  "IFSC code HDFC0000001",
  "dialysis center Alvin TX CMS rating",
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());

for (const q of GOOGLE) {
  try {
    await page.goto("https://www.google.com/search?hl=en&num=20&q=" + encodeURIComponent(q),
                    { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(2200);
    const info = await page.evaluate(() => {
      const t = document.body ? document.body.innerText : "";
      const m = t.match(/(About [\d,]+ results|[\d,]+ results|did not match any documents)/i);
      const hits = Array.from(document.querySelectorAll("a[href]"))
        .map((a) => a.href)
        .filter((u) => (u.indexOf("telegra.ph") >= 0 || u.indexOf("substack.com") >= 0 || u.indexOf("github.com") >= 0))
        .slice(0, 4);
      return { stat: m ? m[0] : null, hits: Array.from(new Set(hits)) };
    });
    console.log("google", q, "->", JSON.stringify(info));
  } catch (e) {
    console.log("google", q, "ERR", String(e).slice(0, 60));
  }
}

for (const q of DDG) {
  try {
    await page.goto("https://html.duckduckgo.com/html/?q=" + encodeURIComponent(q),
                    { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(2200);
    const info = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll("a.result__a")).map((a) => a.href).slice(0, 6);
      const ours = links.filter((u) => u.indexOf("tekify.xyz") >= 0);
      return { n: links.length, ours: ours.slice(0, 3), top: links.slice(0, 2).map((u) => u.slice(0, 80)) };
    });
    console.log("ddg", q, "->", JSON.stringify(info));
  } catch (e) {
    console.log("ddg", q, "ERR", String(e).slice(0, 60));
  }
}
await release(h);
process.exit(0);
