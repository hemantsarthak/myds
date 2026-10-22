const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"cuelinks_pw_state.json"),"utf8"));
  const browser = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const ctx = await browser.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1366,height:900}, locale:"en-IN", timezoneId:"Asia/Kolkata", storageState:state});
  const page = await ctx.newPage();
  for (const u of ["https://www.cuelinks.com/dashboard","https://www.cuelinks.com/publishers/campaigns","https://www.cuelinks.com/users/edit"]) {
    await page.goto(u,{waitUntil:"domcontentloaded",timeout:60000});
    for (let i=0;i<6;i++){ 
      const t = await page.title();
      if (!/just a moment/i.test(t)) break;
      await page.waitForTimeout(5000);
      // try clicking the turnstile checkbox if present
      const fr = page.frames().find(f => /challenges\.cloudflare\.com/.test(f.url()));
      if (fr) { try { await fr.click('input[type=checkbox]', {timeout:2000}); } catch(e){} }
    }
    console.log("=== ", u, "->", page.url(), "|", await page.title());
    const t = (await page.evaluate(()=>document.body.innerText)).replace(/\n{3,}/g,"\n\n");
    console.log(t.slice(0,1200));
    fs.writeFileSync(path.join(SHARED,"cuelinks_pw_state.json"), JSON.stringify(await ctx.storageState(),null,1));
  }
  await browser.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
