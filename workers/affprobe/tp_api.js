const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  const api = [];
  p.on("response", async r => {
    const u = r.url();
    if (!/\.(js|css|png|svg|woff2?|jpg|webp|ico)/.test(u) && /api|graphql|profile|user|account/.test(u)) {
      try { const ct = r.headers()["content-type"]||""; if (/json/.test(ct)) { const t = await r.text(); api.push({u, s:r.status(), body:t.slice(0,700)}); } } catch(e){}
    }
  });
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"networkidle",timeout:60000}).catch(()=>{});
  await p.waitForTimeout(4000);
  for (const a of api.slice(0,25)) { console.log("API", a.s, a.u); console.log("   ", a.body.slice(0,400)); }
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
