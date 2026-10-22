const path=require("path"), fs=require("fs");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
const Q = `query GP($ids:[Int!]!) { brandPrograms(ids:$ids, disableSuppressions:true, showSuspended:true) { id name promos(materialType: PROMO_LINK) { __typename ... on ProgramPromoLink { id text url link erid languages { code } } } } }`;
const IDS = [84,100,111,121,104,594,637,108,47,137,117,120,86,209,180,631,541,629,222,145,93,224,105,175,89,62,44,91];
(async()=>{
  const state = JSON.parse(fs.readFileSync(path.join(SHARED,"travelpayouts_pw_state.json"),"utf8"));
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1440,height:900}, locale:"en-IN", storageState:state});
  const p = await c.newPage();
  await p.goto("https://app.travelpayouts.com/dashboard",{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(2500);
  const out = await p.evaluate(async ({query, ids}) => {
    const r = await fetch("/api/graphql",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query, variables:{ids}})});
    return await r.text();
  }, {query:Q, ids:IDS});
  fs.writeFileSync(path.join(SHARED,"travelpayouts_promolinks.json"), out);
  try {
    const j = JSON.parse(out);
    if (j.errors) { console.log("ERRORS", JSON.stringify(j.errors).slice(0,600)); }
    for (const pr of (j.data && j.data.brandPrograms) || []) {
      console.log("=== ", pr.id, pr.name);
      for (const promo of (pr.promos||[]).slice(0,3)) {
        console.log("   url:", promo.url, "| link:", promo.link, "| erid:", promo.erid);
      }
    }
  } catch(e){ console.log("RAW", out.slice(0,1200)); }
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
