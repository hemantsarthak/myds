const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
const tries = [
 `{ programs(ids:[84]) { id name } }`,
 `{ brandProgram(id:84) { id name } }`,
 `{ brandPrograms(page:1, perPage:2, brandIds:[84]) { id name } }`,
 `{ brandPrograms(ids:[84], disableSuppressions:true) { id name } }`,
 `{ partnerPrograms(ids:[84]) { id name } }`,
];
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(2000);
  for (const q of tries) {
    const out = await p.evaluate(async (query) => {
      const r = await fetch("/api/graphql",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query})});
      return (await r.text()).slice(0,300);
    }, q);
    console.log("Q:", q, "\n  ->", out.replace(/\s+/g," ").slice(0,260));
  }
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
