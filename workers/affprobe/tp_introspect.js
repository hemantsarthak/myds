const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(4000);
  const res = await p.evaluate(async () => {
    const q = `query { __schema { queryType { fields { name args { name type { kind name ofType { name kind } } } } } } }`;
    const r = await fetch("/api/graphql", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({query:q})});
    const j = await r.json();
    return JSON.stringify(j).slice(0, 200000);
  });
  const j = JSON.parse(res);
  if (j.data && j.data.__schema) {
    const names = j.data.__schema.queryType.fields.map(f=>f.name);
    console.log("FIELDS:", names.join(", "));
    const interesting = j.data.__schema.queryType.fields.filter(f=>/marker|promo|link|program|partner|tool|source|balance|payout/i.test(f.name));
    console.log("\nINTERESTING:");
    console.log(JSON.stringify(interesting, null, 1));
  } else console.log(res.slice(0,600));
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
