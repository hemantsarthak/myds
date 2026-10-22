import { getBrowser, release } from "../agentbrowser.mjs";
const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
await page.goto("https://tekify.xyz/insights/hospital-ratings-by-state/", { waitUntil: "domcontentloaded", timeout: 40000 });
await page.waitForTimeout(1500);
const info = await page.evaluate(() => {
  const svgs = Array.from(document.querySelectorAll("svg"));
  return { svgs: svgs.length, bars: document.querySelectorAll("rect").length,
           firstChartWidth: svgs.length ? svgs[svgs.length-1].getBoundingClientRect().width : 0 };
});
console.log(JSON.stringify(info));
await release(h);
process.exit(0);
