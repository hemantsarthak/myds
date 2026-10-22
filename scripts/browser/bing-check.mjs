// Check Bing and DuckDuckGo index coverage for our properties (no account needed).
import { getBrowser, release } from "../agentbrowser.mjs";

const QUERIES = [
  "site:hospitals.tekify.xyz",
  "site:dialysis.tekify.xyz",
  "site:tekify.xyz",
  "site:telegra.ph Tekify",
];
const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());

for (const q of QUERIES) {
  const engines = [
    ["bing", "https://www.bing.com/search?q="],
    ["ddg", "https://html.duckduckgo.com/html/?q="],
  ];
  for (const pair of engines) {
    const engine = pair[0];
    const tpl = pair[1];
    try {
      await page.goto(tpl + encodeURIComponent(q), { waitUntil: "domcontentloaded", timeout: 45000 });
      await page.waitForTimeout(2200);
      const info = await page.evaluate(() => {
        const t = document.body ? document.body.innerText : "";
        const m = t.match(/([\d,]+) results|About ([\d,]+) results|No results/i);
        const anchors = Array.from(document.querySelectorAll("a[href]"));
        const urls = anchors.map((a) => a.href);
        const ours = urls.filter((u) => u.indexOf("tekify.xyz") >= 0 && u.indexOf("bing.com") < 0 && u.indexOf("duckduckgo.com") < 0);
        return { countText: m ? m[0] : null, hits: Array.from(new Set(ours)).slice(0, 4) };
      });
      console.log(engine + " " + q + " -> " + JSON.stringify(info));
    } catch (e) {
      console.log(engine + " " + q + " -> ERR " + String(e).slice(0, 60));
    }
  }
}
await release(h);
process.exit(0);
