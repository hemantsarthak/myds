// Create a Hugging Face account with our own inbox, verify the email, then mint a write token.
// Run after 00:00 UTC (05:30 IST) when the mailbox KV quota resets.
import { execFileSync } from "node:child_process";
import { getBrowser, release } from "../agentbrowser.mjs";

const EMAIL = "huggingface@tekify.xyz";
const USER = "tekifydata";
const PASS = "Tekify!Hf#2026x";

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());

const inbox = () => {
  try {
    return execFileSync("python", ["scripts/ops.py", "inbox", "--latest", "--to", EMAIL], {
      cwd: process.cwd(), encoding: "utf8", timeout: 90000,
    });
  } catch (e) {
    return "INBOX ERROR " + String(e).slice(0, 120);
  }
};

const waitForMail = async (needle, tries = 8) => {
  for (let i = 0; i < tries; i++) {
    await new Promise((r) => setTimeout(r, 10000));
    const out = inbox();
    console.log(`inbox poll ${i + 1}:`, out.slice(0, 300).replace(/\n/g, " | "));
    if (new RegExp(needle, "i").test(out)) return out;
  }
  return null;
};

// 1) signup form
await page.goto("https://huggingface.co/join", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(3500);
const form = await page.evaluate(() => ({
  url: location.href,
  text: (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 300),
  inputs: [...document.querySelectorAll("input")].map((i) => ({ type: i.type, name: i.name || i.id, ph: i.placeholder || "" })).filter((i) => i.type !== "hidden"),
  buttons: [...document.querySelectorAll("button,input[type=submit]")].map((b) => (b.innerText || b.value || "").trim()).filter(Boolean).slice(0, 8),
}));
console.log("form:", JSON.stringify(form, null, 1));

await page.fill('input[name="email"], input[type="email"]', EMAIL).catch(() => {});
await page.fill('input[name="password"], input[type="password"]', PASS).catch(() => {});
await page.fill('input[name="username"]', USER).catch(() => {});
const terms = page.locator('input[type="checkbox"]').first();
if (await terms.count()) await terms.check({ force: true }).catch(() => {});
await page.waitForTimeout(500);
await page.getByRole("button", { name: /create account|sign up|next|continue|register/i }).first()
  .click({ timeout: 8000 }).catch(() => {});
await page.waitForTimeout(6000);
const afterSubmit = await page.evaluate(() => (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 300));
console.log("after submit:", afterSubmit);

// 2) email confirmation
const mail = await waitForMail("huggingface|confirm|verify");
if (mail) {
  const m = mail.match(/https:\/\/[^\s"']*huggingface\.co[^\s"']*(confirm|verify)[^\s"']*/i);
  console.log("confirmation link:", m ? m[0].slice(0, 120) : "NOT FOUND in mail");
  if (m) {
    await page.goto(m[0], { waitUntil: "domcontentloaded", timeout: 45000 }).catch(() => {});
    await page.waitForTimeout(5000);
    console.log("after confirm:", page.url());
  }
}

// 3) mint a write token
await page.goto("https://huggingface.co/settings/tokens", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(3000);
const tokPage = await page.evaluate(() => ({
  url: location.href,
  text: (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 300),
  buttons: [...document.querySelectorAll("button")].map((b) => (b.innerText || "").trim()).filter(Boolean).slice(0, 10),
}));
console.log("tokens page:", JSON.stringify(tokPage, null, 1));
await release(h);
process.exit(0);
