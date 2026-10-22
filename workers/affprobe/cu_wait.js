const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"cuelinks_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1366,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  await p.goto("https://www.cuelinks.com/dashboard",{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(12000);
  console.log("URL", p.url(), "|", await p.title());
  // if challenged, wait for turnstile to auto-solve
  for (let i=0;i<12;i++){
    const t = await p.title();
    if (!/just a moment/i.test(t)) break;
    await p.waitForTimeout(5000);
  }
  console.log("AFTER WAIT", p.url(), "|", await p.title());
  const t=(await p.evaluate(()=>document.body.innerText)).replace(/\n{3,}/g,"\n\n");
  console.log(t.slice(0,1500));
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
