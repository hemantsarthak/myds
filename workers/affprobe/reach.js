const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
(async()=>{
  const browser = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const ctx = await browser.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1366,height:900}, locale:"en-IN", timezoneId:"Asia/Kolkata"});
  const page = await ctx.newPage();
  for (const u of ["https://www.namecheap.com/affiliates/","https://www.vultr.com/affiliate/","https://signup.cj.com/member/signup/publisher/"]) {
    try {
      await page.goto(u,{waitUntil:"domcontentloaded",timeout:45000});
      for (let i=0;i<8;i++){ if(!/just a moment/i.test(await page.title())) break; await page.waitForTimeout(4000); }
      console.log("=== ",u,"->",page.url(),"|",await page.title());
      const t=(await page.evaluate(()=>document.body.innerText)).replace(/\n{3,}/g,"\n\n");
      console.log(t.slice(0,700));
    } catch(e){ console.log("ERR",u,e.message.slice(0,120)); }
  }
  await browser.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
