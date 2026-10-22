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
  const btnState = async (label) => {
    const d = await page.$eval("#profile_personal-info-save-button", b => b.disabled);
    console.log(`after ${label}: continue disabled=${d}`);
  };
  await btnState("load");
  await page.fill("#profile_personal-info-first-name", "Tekify"); await btnState("firstname");
  await page.fill("#profile_personal-info-last-name", "Ads"); await btnState("lastname");
  await page.fill("#profile_personal-info-email", "monetag@tekify.xyz"); await btnState("email");
  // inspect country select value
  const vals = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll('input[id^="react-select"]').forEach(i => {
      const root = i.closest('[class*="container"]') || i.parentElement;
      out.push({id:i.id, val:i.value, ariaExpanded:i.getAttribute("aria-expanded"), parentText:(root?root.innerText:"").slice(0,100)});
    });
    // find visible label texts around selects
    return out;
  });
  console.log("SELECTS", JSON.stringify(vals));
  const allText = await page.innerText("body");
  console.log("BODY:", allText.slice(0,1200));
  await browser.close();
})().catch(e => { console.error("FATAL", e.message); process.exit(1); });
