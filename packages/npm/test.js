// Smoke test: node test.js (needs network).
const t = require("./index.js");

(async () => {
  const zip = await t.zipCode("90210");
  console.log("zip:", zip);
  const h = await t.hospitals("Johns Hopkins", 2);
  console.log("hospitals:", h);
  const b = await t.ifscBank("HDFC");
  console.log("ifsc branches:", b.length, b[0]);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
