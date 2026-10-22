/**
 * tekify-data — keyless client for the Tekify open-data JSON endpoints.
 *
 * Data sources: US Census Bureau, CMS, NCES/IPEDS, GeoNames (CC BY), OurAirports, Razorpay IFSC (MIT).
 * Every endpoint is CORS-enabled and needs no API key. Docs: https://hemantsarthak.github.io/myds/data.html
 */

const BASE = {
  zip: "https://zipcodes.tekify.xyz/data/zips.json",
  places: "https://places.tekify.xyz/data/places.json",
  colleges: "https://colleges.tekify.xyz/data/colleges.json",
  hospitals: "https://hospitals.tekify.xyz/data/hospitals.json",
  nursingHomes: "https://nursinghomes.tekify.xyz/data/nursinghomes.json",
  homeHealth: "https://homehealth.tekify.xyz/data/homehealth.json",
  dialysis: "https://dialysis.tekify.xyz/data/dialysis.json",
  airports: "https://airportcodes.tekify.xyz/data/airports.json",
  areaCodes: "https://areacodes.tekify.xyz/data/search.json",
  ifscBank: (bank) => `https://ifsccodes.tekify.xyz/data/bank/${encodeURIComponent(String(bank).toUpperCase())}.json`,
};

const FIELDS = {
  zip: ["zip", "city", "state", "county", "population", "timezone"],
  places: ["name", "state", "county", "population", "url"],
  colleges: ["name", "city", "state", "unitid", "url"],
  hospitals: ["name", "city", "state", "rating", "url"],
  nursingHomes: ["name", "city", "state", "rating", "url"],
  homeHealth: ["name", "city", "state", "rating", "url"],
  dialysis: ["name", "city", "state", "rating", "url"],
  airports: ["iata", "ident", "icao", "name", "city", "country"],
  areaCodes: ["code", "label", "url"],
  ifsc: ["ifsc", "branch", "district", "state"],
};

const cache = new Map();

async function load(url) {
  if (cache.has(url)) return cache.get(url);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`tekify-data: HTTP ${res.status} for ${url}`);
  const rows = await res.json();
  cache.set(url, rows);
  return rows;
}

/** Compact array-of-arrays rows → array of named objects. */
function toObjects(rows, fields) {
  return rows.map((row) => {
    const out = {};
    fields.forEach((f, i) => {
      out[f] = row[i];
    });
    return out;
  });
}

function matches(row, query, keys) {
  const hay = keys.map((k) => String(row[k] ?? "")).join(" ").toLowerCase();
  return hay.includes(String(query).toLowerCase());
}

/**
 * Look up a US ZIP code.
 * @param {string} zip
 * @returns {Promise<object|null>}
 */
async function zipCode(zip) {
  const rows = await load(BASE.zip);
  const row = rows.find((r) => String(r[0]) === String(zip));
  return row ? toObjects([row], FIELDS.zip)[0] : null;
}

/** Hospitals matching a name or city. */
async function hospitals(query, limit = 20) {
  const rows = toObjects(await load(BASE.hospitals), FIELDS.hospitals);
  return rows.filter((r) => matches(r, query, ["name", "city", "state"])).slice(0, limit);
}

/** Nursing homes matching a name or city. */
async function nursingHomes(query, limit = 20) {
  const rows = toObjects(await load(BASE.nursingHomes), FIELDS.nursingHomes);
  return rows.filter((r) => matches(r, query, ["name", "city", "state"])).slice(0, limit);
}

/** Home-health agencies matching a name or city. */
async function homeHealth(query, limit = 20) {
  const rows = toObjects(await load(BASE.homeHealth), FIELDS.homeHealth);
  return rows.filter((r) => matches(r, query, ["name", "city", "state"])).slice(0, limit);
}

/** Dialysis facilities matching a name or city. */
async function dialysis(query, limit = 20) {
  const rows = toObjects(await load(BASE.dialysis), FIELDS.dialysis);
  return rows.filter((r) => matches(r, query, ["name", "city", "state"])).slice(0, limit);
}

/** Colleges matching a name or city. */
async function colleges(query, limit = 20) {
  const rows = toObjects(await load(BASE.colleges), FIELDS.colleges);
  return rows.filter((r) => matches(r, query, ["name", "city", "state"])).slice(0, limit);
}

/** US places matching a name, county or state. */
async function places(query, limit = 20) {
  const rows = toObjects(await load(BASE.places), FIELDS.places);
  return rows.filter((r) => matches(r, query, ["name", "county", "state"])).slice(0, limit);
}

/** Airports matching an IATA/ICAO code, name or city. */
async function airports(query, limit = 20) {
  const rows = toObjects(await load(BASE.airports), FIELDS.airports);
  return rows.filter((r) => matches(r, query, ["iata", "ident", "icao", "name", "city", "country"])).slice(0, limit);
}

/** Area codes matching a code or place name. */
async function areaCodes(query, limit = 20) {
  const rows = toObjects(await load(BASE.areaCodes), FIELDS.areaCodes);
  return rows.filter((r) => matches(r, query, ["code", "label"])).slice(0, limit);
}

/** Indian bank branches for a bank code (e.g. "HDFC"). */
async function ifscBank(bank) {
  const rows = toObjects(await load(BASE.ifscBank(bank)), FIELDS.ifsc);
  return rows;
}

module.exports = {
  zipCode,
  hospitals,
  nursingHomes,
  homeHealth,
  dialysis,
  colleges,
  places,
  airports,
  areaCodes,
  ifscBank,
  endpoints: BASE,
};
