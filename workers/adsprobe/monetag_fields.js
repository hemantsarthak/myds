const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: true, args: ["--disable-blink-features=AutomationControlled"] });
  const ctx = await browser.newContext({ viewport: { width: 1366, height: 900 }, locale: "en-US",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" });
  const page = await ctx.newPage();
  await page.goto("https://publishers.monetag.com/signUp", { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(2000);
  const ok = page.locator('text=OK, THANKS'); if (await ok.count()) { await ok.first().click().catch(()=>{}); await page.waitForTimeout(400); }
  await page.click("#create-account-with-email-button");
  await page.waitForTimeout(1500);
  const info = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll("input, select, textarea, button").forEach(e => {
      out.push({tag:e.tagName, type:e.type||e.getAttribute("type"), id:e.id, name:e.getAttribute("name"), required:e.required, ariaRequired:e.getAttribute("aria-required"), disabled:e.disabled, cls:(e.className||"").toString().slice(0,80)});
    });
    const labels = [...document.querySelectorAll("label")].map(l => ({t:(l.innerText||"").trim().slice(0,80), for:l.getAttribute("for")}));
    return {out, labels, bodyLen: document.body.innerHTML.length};
  });
  console.log(JSON.stringify(info.out, null, 0));
  console.log("LABELS", JSON.stringify(info.labels));
  // inspect react-select option labels for country and messenger
  const selTexts = await page.evaluate(() => {
    const res = [];
    document.querySelectorAll('[class*="select"]').forEach(el => res.push((el.innerText||"").slice(0,120)));
    return res.slice(0,20);
  });
  console.log("SELECTTEXT", JSON.stringify(selTexts));
  await browser.close();
})().catch(e => { console.error("FATAL", e.message); process.exit(1); });
