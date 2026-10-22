const { chromium } = require("playwright");
const fs = require("fs");
(async () => {
  const headless = process.argv[2] !== "headful";
  const browser = await chromium.launch({
    channel: "chrome",
    headless,
    args: ["--disable-blink-features=AutomationControlled", "--no-sandbox"],
  });
  const ctx = await browser.newContext({
    viewport: { width: 1366, height: 900 },
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    locale: "en-US",
  });
  const page = await ctx.newPage();
  const reqs = [];
  page.on("request", (r) => { if (r.url().includes("/api/") || r.url().includes("captcha")) reqs.push(r.method()+" "+r.url()); });
  const resp = [];
  page.on("response", async (r) => { if (r.url().includes("/api/")) resp.push(r.status()+" "+r.url()); });
  await page.goto("https://publishers.monetag.com/signUp", { waitUntil: "networkidle", timeout: 60000 }).catch(e=>console.log("goto:", e.message));
  await page.waitForTimeout(3000);
  fs.mkdirSync("workers/adsprobe/shots", { recursive: true });
  await page.screenshot({ path: "workers/adsprobe/shots/monetag_signup.png", fullPage: true });
  console.log("URL:", page.url());
  console.log("TITLE:", await page.title());
  const inputs = await page.$$eval("input, select, textarea, button", els => els.map(e => ({tag:e.tagName, type:e.getAttribute("type"), name:e.getAttribute("name"), id:e.id, ph:e.getAttribute("placeholder"), txt:(e.innerText||"").slice(0,40)})));
  console.log("CONTROLS:", JSON.stringify(inputs, null, 1).slice(0, 4000));
  console.log("TEXT:", (await page.innerText("body")).slice(0, 1500));
  console.log("REQS:", JSON.stringify(reqs.slice(0,30), null, 1));
  console.log("RESP:", JSON.stringify(resp.slice(0,30), null, 1));
  await browser.close();
})().catch(e => { console.error("FATAL", e); process.exit(1); });
