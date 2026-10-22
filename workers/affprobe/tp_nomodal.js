const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  for (const u of ["https://app.travelpayouts.com/library","https://app.travelpayouts.com/programs","https://app.travelpayouts.com/tools/link-generator"]) {
    await p.goto(u,{waitUntil:"domcontentloaded",timeout:45000});
    await p.waitForTimeout(3500);
    // hide overlay modals
    await p.addStyleTag({content:"[class*=modal],[class*=Modal],[class*=overlay],[class*=Overlay]{display:none!important}"});
    await p.waitForTimeout(800);
    const txt = (await p.evaluate(()=>document.body.innerText)).replace(/\n{3,}/g,"\n\n");
    console.log("=====", u, "->", p.url(), "|", (await p.title()).slice(0,40));
    console.log(txt.slice(0,900));
  }
  await p.screenshot({path:path.join(__dirname,"tp_nomodal.png")});
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
