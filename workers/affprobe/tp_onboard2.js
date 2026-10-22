const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", timezoneId:"Asia/Kolkata", storageState:state});
  const p = await c.newPage();
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(4000);
  for (let i=0;i<3;i++){
    const btn = await p.$('button:has-text("Continue")');
    if (!btn) break;
    await Promise.all([p.waitForLoadState("domcontentloaded").catch(()=>{}), btn.click().catch(()=>{})]);
    await p.waitForTimeout(5000);
    console.log("STEP",i,p.url());
  }
  console.log("FINAL URL", p.url(), "|", await p.title());
  console.log((await p.evaluate(()=>document.body.innerText)).replace(/\n{3,}/g,"\n\n").slice(0,3000));
  fs.writeFileSync(path.join(SHARED,"travelpayouts_pw_state.json"), JSON.stringify(await c.storageState(),null,1));
  await p.screenshot({path:path.join(__dirname,"tp_final.png")});
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
