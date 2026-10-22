# What 121,000 pages of public data taught me about American healthcare

*Draft for Medium.*

---

Over the past few days I built twelve reference directories from public datasets — 121,000 pages of ZIP codes, bank branch codes, airports, colleges, hospitals, nursing homes, home health agencies, dialysis centres and calculators. The healthcare data came from CMS, the agency that runs Medicare, and it is fully public: every hospital rating, every nursing-home inspection, every dialysis facility's outcome measures.

A few things stood out.

## 1. The gap between states is bigger than the gap between hospitals

Hospital star ratings vary enormously by state: about 79% of Utah's rated hospitals are four stars or better, against about 13% in Mississippi. That is not a small statistical wobble — it is a different standard of care depending on where you live.

Some of it is case mix and reporting. Some of it is poverty, rurality and insurance coverage. But the size of the gap is the story, and it is visible in a public dataset anyone can download.

## 2. Most hospitals have an emergency department — but not all

83% of hospitals in the CMS directory report emergency services. The other 17% are specialty, psychiatric, rehabilitation or critical-access facilities. In an emergency, the closest hospital is not always one that can treat you. It takes two minutes to check before you need it.

## 3. Nursing-home staffing is the number families should look at

The overall star rating is a blend of inspections, staffing and quality measures. But staffing — nurse hours per resident per day, and how often staff turn over — is the measure that most directly maps to what daily life is like in a home. High turnover is a warning sign even when the hours look adequate.

## 4. Dialysis is where the data is richest

Dialysis facilities are rated on patient survival, hospitalisation, readmission, transfusion, emergency-department visits and transplant waitlisting. Each measure is compared with what CMS expects for the facility's patients. For anyone choosing a centre, the individual measures — and whether the facility offers home dialysis training — matter more than the star rating.

## 5. Open data is still hard to use

Every one of these facts comes from a public file. Almost none of it is easy to find: the files are large, the columns are cryptic, and the agency lookup tools are designed for compliance rather than curiosity. That gap — public data, private usability — is why the directories exist.

## Where the data lives

Everything is free, source-stated and needs no account:

- [US Hospitals](https://hospitals.tekify.xyz) — 5,888 hospitals with CMS ratings
- [US Nursing Homes](https://nursinghomes.tekify.xyz) — 15,056 facilities with staffing
- [US Home Health](https://homehealth.tekify.xyz) — 12,777 agencies
- [US Dialysis Centers](https://dialysis.tekify.xyz) — 7,490 facilities
- [US Colleges](https://colleges.tekify.xyz) — 6,056 institutions
- [US ZIP Codes](https://zipcodes.tekify.xyz), [Places & Counties](https://places.tekify.xyz), [Airport Codes](https://airportcodes.tekify.xyz), [Area Codes](https://areacodes.tekify.xyz), [IFSC Codes India](https://ifsccodes.tekify.xyz), [Calculators](https://calculators.tekify.xyz)

The analyses are at [tekify.xyz/insights](https://tekify.xyz/insights/), the data documentation at [this page](https://hemantsarthak.github.io/myds/data.html), and the build system is public on [GitHub](https://github.com/hemantsarthak/myds).

---

*All datasets are public domain or openly licensed (US Census Bureau, CMS, NCES/IPEDS, GeoNames, OurAirports, Razorpay IFSC).*
