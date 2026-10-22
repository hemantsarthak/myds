// Ad-serving diagnostic: load one of our pages in the shared agent browser and record
// everything that looks like an ad request/response plus any frames the ad scripts create.
import { getBrowser, release } from "./agentbrowser.mjs";

const URLS = [
  "https://ifsccodes.tekify.xyz/ifsc/ABHY0065102/",
  "https://hospitals.tekify.xyz/hospital/adventhealth-castle-rock/",
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
const events = [];
page.on("request", (r) => {
  const u = r.url();
  if (/unfoldedtrade|subtle-injury|hilltop|popads|propeller|adsterra|doubleclick|googlesyndication/i.test(u)) {
    events.push(["REQ", u.slice(0, 160)]);
  }
});
page.on("response", (r) => {
  const u = r.url();
  if (/unfoldedtrade|subtle-injury|hilltop/i.test(u)) {
    events.push(["RES", r.status(), u.slice(0, 160)]);
  }
});
page.on("console", (m) => {
  const t = m.text();
  if (/ad|block|error|refus/i.test(t)) events.push(["CONSOLE", m.type(), t.slice(0, 140)]);
});

for (const url of URLS) {
  events.push(["NAV", url]);
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
  } catch (e) {
    events.push(["GOTO-ERR", String(e).slice(0, 120)]);
    continue;
  }
  await page.waitForTimeout(9000);
  const info = await page.evaluate(() => {
    const scripts = [...document.querySelectorAll("script[src]")].map((s) => s.src);
    const adish = scripts.filter((s) => /unfoldedtrade|subtle-injury|hilltop/i.test(s));
    const iframes = [...document.querySelectorAll("iframe")].map((f) => f.src);
    return {
      adScripts: adish.length,
      adScriptSrcs: adish.map((s) => s.slice(0, 90)),
      iframeCount: iframes.length,
      iframes: iframes.slice(0, 6),
      bodyChildren: document.body ? document.body.children.length : 0,
    };
  });
  events.push(["DOM", url, JSON.stringify(info).slice(0, 700)]);
}

console.log(JSON.stringify(events, null, 1));
await release(h);
process.exit(0);
