import { getBrowser, release } from "../agentbrowser.mjs";
const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
for (const q of ["site:hemantsarthak.github.io", "site:tekify.xyz", "hemantsarthak.github.io myds"]) {
  try {
    await page.goto("https://www.bing.com/search?q=" + encodeURIComponent(q), { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(3000);
    const info = await page.evaluate(() => {
      const t = document.body ? document.body.innerText : "";
      const stat = (t.match(/([\d,]+) results|No results/i) || [null])[0];
      const links = Array.from(document.querySelectorAll("a[href]")).map((a) => a.href)
        .filter((u) => u.indexOf("github.io") >= 0 || u.indexOf("tekify.xyz") >= 0);
      return { stat: stat, ours: Array.from(new Set(links)).slice(0, 5), blocked: /captcha|verify you are human/i.test(t) };
    });
    console.log(q, "->", JSON.stringify(info));
  } catch (e) {
    console.log(q, "ERR", String(e).slice(0, 80));
  }
}
await release(h);
process.exit(0);
