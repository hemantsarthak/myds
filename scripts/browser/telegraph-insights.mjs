import { getBrowser, release } from "../agentbrowser.mjs";

const ARTICLES = [
  {
    title: "Which US states have the best-rated hospitals? (CMS star ratings by state)",
    blocks: [
      "<p>CMS gives every US hospital an overall rating from one to five stars. Aggregated by state, the share of four- and five-star hospitals ranges from about 80% down to about 14%.</p>",
      "<h3>The top of the table</h3>",
      "<p>Utah leads with roughly 79% of its rated hospitals at four stars or better, followed by Colorado (73%) and Wisconsin (64%). At the other end, Mississippi has about 14%.</p>",
      "<p>The full state-by-state table, with hospital counts, rated counts and average ratings, is published here: <a href=\"https://tekify.xyz/insights/hospital-ratings-by-state/\">CMS hospital ratings by state</a>. You can look up any individual hospital at <a href=\"https://hospitals.tekify.xyz\">US Hospitals</a>.</p>",
      "<h3>How to read it</h3>",
      "<p>The share of top-rated hospitals and the average rating are different measures. A state where many hospitals are unrated can post a flattering average from a small rated set, which is why the table shows both. Ratings reflect mortality, safety, readmission, patient experience and timely care, each compared with what CMS expects for similar patients.</p>"
    ]
  },
  {
    title: "America's largest nursing-home chains, counted from CMS data",
    blocks: [
      "<p>CMS records the chain behind every nursing home. Counting facilities by chain shows a concentrated industry: the ten largest operators run thousands of facilities between them.</p>",
      "<h3>The biggest operators</h3>",
      "<p>The largest chains each operate hundreds of nursing homes; average CMS star ratings among the biggest operators differ, and the full ranking — with facility counts, certified beds and average ratings — is here: <a href=\"https://tekify.xyz/insights/largest-nursing-home-chains/\">largest nursing-home chains</a>.</p>",
      "<h3>Why chain affiliation matters</h3>",
      "<p>Staffing policy, training and management are often set at chain level, and CMS publishes chain-level averages alongside facility ratings for that reason. To check an individual home, including its staffing and inspection results, use <a href=\"https://nursinghomes.tekify.xyz\">US Nursing Homes</a>.</p>"
    ]
  }
];

const h = await getBrowser();
const page = h.context.pages()[0] || (await h.context.newPage());
for (const art of ARTICLES) {
  try {
    await page.goto("https://telegra.ph/", { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(2300);
    const markup = "<h3>" + art.title + "</h3>" + art.blocks.join("");
    await page.evaluate((html) => {
      const ed = document.querySelector(".ql-editor");
      ed.innerHTML = html;
      ed.dispatchEvent(new Event("input", { bubbles: true }));
    }, markup);
    await page.waitForTimeout(1000);
    await page.getByRole("button", { name: /publish/i }).first().click({ timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(3200);
    console.log("published:", page.url());
  } catch (e) {
    console.log("failed:", art.title, String(e).slice(0, 80));
  }
}
await release(h);
process.exit(0);
