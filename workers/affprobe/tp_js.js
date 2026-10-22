const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  const js = [];
  p.on("response", r => { const u=r.url(); if (/\.js(\?|$)/.test(u) && /travelpayouts|avs\.io/.test(u)) js.push(u); });
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"networkidle",timeout:60000}).catch(()=>{});
  await p.waitForTimeout(2000);
  fs.writeFileSync("tp_js_urls.json", JSON.stringify([...new Set(js)],null,1));
  console.log("js files:", [...new Set(js)].length);
  // download them
  const fsx = require("fs");
  require("fs").mkdirSync("tp_js", {recursive:true});
  let i=0;
  for (const u of [...new Set(js)]) {
    try {
      const buf = await p.evaluate(async (url)=>{ const r = await fetch(url); return await r.text(); }, u);
      fsx.writeFileSync(path.join("tp_js", `b${i++}.js`), buf);
    } catch(e){ console.log("ERR", u.slice(0,60)); }
  }
  console.log("downloaded", i);
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
