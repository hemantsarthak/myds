const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  const bodies = [];
  p.on("request", r => { if (r.url().includes("/api/graphql") && r.method()==="POST") { try { bodies.push(r.postData()||""); } catch(e){} } });
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"networkidle",timeout:60000}).catch(()=>{});
  await p.waitForTimeout(3000);
  fs.writeFileSync("tp_gql_bodies.json", JSON.stringify(bodies,null,1));
  console.log("captured", bodies.length, "bodies");
  // print operation names
  for (const bd of bodies) { try { const j=JSON.parse(bd); console.log("OP:", (j.operationName||"(anon)"), "| keys:", Object.keys(j)); if (j.query && j.query.length<300) console.log("   Q:", j.query); } catch(e){ console.log("raw", bd.slice(0,150)); } }
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
