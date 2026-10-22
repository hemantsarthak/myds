const path=require("path"), fs=require("fs"), crypto=require("crypto");
const { chromium } = require("playwright");
const SHARED = path.resolve(__dirname,"..","..","shared");
(async()=>{
  const email = "travelpayouts@tekify.xyz";
  const pwd = "Tp" + crypto.randomBytes(4).toString("hex") + "!9A"; // 3-16? need 8+ w/ upper/lower/digit/special
  const b = await chromium.launch({headless:true, channel:"chrome", args:["--disable-blink-features=AutomationControlled"]});
  const c = await b.newContext({userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36", viewport:{width:1366,height:900}, locale:"en-IN", timezoneId:"Asia/Kolkata"});
  const p = await c.newPage();
  const url = "https://passport.travelpayouts.com/registration?client_id=b0e02fcc-0ab4-4b2c-a164-742762783a4e&response_type=code&redirect_uri=https%3A%2F%2Fapp.travelpayouts.com%2Fapi%2Fauth%2Fcallback&locale=en";
  await p.goto(url,{waitUntil:"domcontentloaded",timeout:60000});
  await p.waitForTimeout(3000);
  await p.fill('input[name=email]', email);
  await p.fill('input[name=password]', pwd);
  await Promise.all([p.waitForLoadState("domcontentloaded").catch(()=>{}), p.click('button[type=submit]')]);
  await p.waitForTimeout(6000);
  console.log("URL", p.url(), "|", await p.title());
  console.log((await p.evaluate(()=>document.body.innerText)).slice(0,1200));
  fs.writeFileSync(path.join(SHARED,"travelpayouts_signup_attempt.json"), JSON.stringify({email,password:pwd,url:p.url()},null,1));
  fs.writeFileSync(path.join(SHARED,"travelpayouts_pw_state.json"), JSON.stringify(await c.storageState(),null,1));
  await p.screenshot({path:path.join(__dirname,"tp_after_submit.png")});
  await b.close();
})().catch(e=>{console.error("FATAL",e.message);process.exit(1)});
