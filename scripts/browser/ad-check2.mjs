import { getBrowser, release } from "../agentbrowser.mjs";
const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
const reqs = [];
page.on("request", (r) => { if (/unfoldedtrade|subtle-injury|hilltop|popunder|push/i.test(r.url())) reqs.push(r.url().slice(0, 90)); });
await page.goto("https://hospitals.tekify.xyz/hospital/edgerton-hospital-and-health-services/", { waitUntil: "domcontentloaded", timeout: 40000 });
await page.waitForTimeout(5000);
const info = await page.evaluate(() => ({
  scripts: Array.from(document.querySelectorAll("script[src]")).map((s) => s.src).filter((u) => /unfoldedtrade|subtle-injury/.test(u)).length,
  iframes: document.querySelectorAll("iframe").length,
}));
console.log(JSON.stringify({ adRequests: reqs.length, sample: reqs.slice(0, 3), ...info }));
await release(h);
process.exit(0);
