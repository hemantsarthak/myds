// Create a Zenodo account with our own inbox, verify the email, then mint a deposit token.
import { execFileSync } from "node:child_process";
import { getBrowser, release } from "../agentbrowser.mjs";

const EMAIL = "zenodo@tekify.xyz";
const USER = "tekifydata";
const PASS = "Tekify!Zen#2026x";
const FULLNAME = "Tekify Data";

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

await page.goto("https://zenodo.org/signup/", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(3000);
const form = await page.evaluate(() => ({
  url: location.href,
  text: (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 300),
  inputs: [...document.querySelectorAll("input")].map((i) => ({ type: i.type, name: i.name || i.id, ph: i.placeholder || "" })).filter((i) => i.type !== "hidden").slice(0, 12),
  buttons: [...document.querySelectorAll("button,input[type=submit]")].map((b) => (b.innerText || b.value || "").trim()).filter(Boolean).slice(0, 8),
}));
console.log("form:", JSON.stringify(form, null, 1));

await page.fill('input[name="email"], input[type="email"]', EMAIL).catch(() => {});
await page.fill('input[name="password"], input[type="password"]', PASS).catch(() => {});
await page.fill('input[name="full_name"], input[name="name"]', FULLNAME).catch(() => {});
await page.fill('input[name="username"]', USER).catch(() => {});
await page.waitForTimeout(500);
await page.getByRole("button", { name: /sign up|register|create/i }).first().click({ timeout: 8000 }).catch(() => {});
await page.waitForTimeout(6000);
const afterSubmit = await page.evaluate(() => (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 300));
console.log("after submit:", afterSubmit);

for (let i = 0; i < 8; i++) {
  await new Promise((r) => setTimeout(r, 10000));
  const out = inbox();
  console.log(`inbox poll ${i + 1}:`, out.slice(0, 250).replace(/\n/g, " | "));
  const m = out.match(/https:\/\/zenodo\.org[^\s"']*(confirm|verify)[^\s"']*/i);
  if (m) {
    console.log("confirmation link:", m[0]);
    await page.goto(m[0], { waitUntil: "domcontentloaded", timeout: 45000 }).catch(() => {});
    await page.waitForTimeout(4000);
    console.log("after confirm:", page.url());
    break;
  }
}
await page.goto("https://zenodo.org/account/settings/applications/", { waitUntil: "domcontentloaded", timeout: 45000 });
await page.waitForTimeout(3000);
const tokPage = await page.evaluate(() => ({
  url: location.href,
  text: (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 300),
  buttons: [...document.querySelectorAll("button,a")].map((b) => (b.innerText || "").trim()).filter(Boolean).slice(0, 10),
}));
console.log("tokens page:", JSON.stringify(tokPage, null, 1));
await release(h);
process.exit(0);
