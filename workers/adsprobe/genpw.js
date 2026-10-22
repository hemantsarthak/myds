const crypto = require("crypto");
const fs = require("fs");
const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";
let pw = "";
while (pw.length < 20) { const b = crypto.randomBytes(1)[0]; if (b < 248 && chars[b % chars.length]) pw += chars[b % chars.length]; }
pw += "!7Xk";
fs.mkdirSync("shared", { recursive: true });
fs.writeFileSync("shared/monetag_signup.json", JSON.stringify({ email: "monetag@tekify.xyz", password: pw, created: new Date().toISOString() }, null, 2));
console.log("wrote shared/monetag_signup.json", pw.length);
