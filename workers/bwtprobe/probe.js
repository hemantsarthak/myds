// probe.js — Playwright recon for Microsoft signup / Bing Webmaster Tools.
// Usage:
//   node probe.js dump <url>
//   node probe.js shot <url> <out.png>
// Read-only: dumps status, title, visible text, inputs/buttons/links so we can plan the flow.
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");
const HERE = __dirname;

const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36";

async function newCtx(headless = true) {
  const browser = await chromium.launch({
    headless,
    channel: "chrome",
    args: ["--disable-blink-features=AutomationControlled"],
  });
  const ctx = await browser.newContext({
    userAgent: UA,
    viewport: { width: 1366, height: 900 },
    locale: "en-US",
    timezoneId: "Asia/Kolkata",
  });
  await ctx.addInitScript(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => undefined });
  });
  return { browser, ctx };
}

async function bodyText(page) {
  return (await page.evaluate(() => (document.body ? document.body.innerText : "")))
    .replace(/\n{3,}/g, "\n\n")
    .slice(0, 4000);
}

async function describe(page) {
  return await page.evaluate(() => {
    const vis = (el) => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    };
    const q = (sel) =>
      Array.from(document.querySelectorAll(sel))
        .filter(vis)
        .map((el) => ({
          tag: el.tagName.toLowerCase(),
          type: el.getAttribute("type") || "",
          id: el.id || "",
          name: el.getAttribute("name") || "",
          label: (el.getAttribute("aria-label") || el.getAttribute("placeholder") || el.innerText || "").trim().slice(0, 80),
          href: el.getAttribute("href") || "",
        }))
        .slice(0, 40);
    return { url: location.href, title: document.title, inputs: q("input,select,textarea"), buttons: q("button,[role=button],input[type=submit]"), links: q("a") };
  });
}

async function main() {
  const [cmd, ...args] = process.argv.slice(2);
  const headless = process.env.HEADFUL ? false : true;
  const { browser, ctx } = await newCtx(headless);
  const page = await ctx.newPage();
  page.setDefaultTimeout(30000);
  try {
    if (cmd === "dump" || cmd === "shot") {
      const r = await page.goto(args[0], { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.waitForTimeout(4000);
      console.log("STATUS", r && r.status());
      console.log("FINAL_URL", page.url());
      const d = await describe(page);
      console.log("TITLE", d.title);
      console.log("\n--- TEXT ---\n" + (await bodyText(page)));
      console.log("\n--- INPUTS ---");
      for (const i of d.inputs) console.log(JSON.stringify(i));
      console.log("\n--- BUTTONS ---");
      for (const b of d.buttons) console.log(JSON.stringify(b));
      console.log("\n--- LINKS ---");
      for (const l of d.links) console.log(JSON.stringify(l));
      if (cmd === "shot") {
        await page.screenshot({ path: path.join(HERE, args[1] || "shot.png"), fullPage: true });
        console.log("SHOT", args[1] || "shot.png");
      }
    } else {
      console.log("unknown cmd", cmd);
    }
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error("FATAL", e.message);
  process.exit(1);
});
