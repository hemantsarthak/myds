#!/usr/bin/env python3
"""catalog.py — assemble every calculator and the category structure."""
import calcs_conv
import calcs_dates
import calcs_health
import calcs_investing
import calcs_loans
import calcs_money2
import calcs_money3
import calcs_salary

CATS = [
    dict(id="loans", name="Loans", title="Loan Calculators — Payments, Mortgages and Debt",
         desc="Calculate loan payments, mortgage costs, amortisation, auto and student loans, "
              "credit card payoff, affordability and refinance break-even.",
         lede="Work out what borrowing really costs: monthly payments, total interest, amortisation "
              "schedules and the break-even point where a refinance or a purchase starts paying off.",
         intro="""<p>Every calculator in this section uses the same core idea: a fixed-rate loan has a
constant payment, and each payment splits between interest on the outstanding balance and principal
that reduces it. Because interest is charged on the balance, the split changes every month even
though the payment does not.</p>
<p>Start with the payment calculator for a quick cost check, then use the amortisation tool to see
how the balance actually falls. The affordability and rent-vs-buy tools are different: they answer
“should I borrow this much at all?” rather than “what will it cost?”.</p>"""),
    dict(id="investing", name="Investing", title="Investment Calculators — Growth, Returns and Inflation",
         desc="Compound interest, savings goals, retirement projections, 401(k) growth, inflation, "
              "ROI, CAGR, APY and simple interest calculators.",
         lede="See how money grows over time — and what it is really worth after inflation, fees and "
              "the difference between nominal and effective returns.",
         intro="""<p>Investment projections are all variations on compounding: a starting balance, a
regular contribution and a rate of return. The calculators here let you vary each factor
separately so you can see which one matters most for your goal.</p>
<p>Treat every projection as a scenario, not a forecast. Constant-return models hide the volatility
of real markets; they are useful for planning ranges and for comparing two decisions, not for
predicting an exact balance.</p>"""),
    dict(id="salary", name="Salary & Tax", title="Salary and Tax Calculators — Pay, Take-Home and Sales Tax",
         desc="Convert hourly pay to salary, calculate overtime and take-home pay, tips, discounts, "
              "sales tax, VAT and GST.",
         lede="Turn gross pay into something you can plan with: take-home pay, overtime, hourly "
              "equivalents, tips and the tax added to (or hidden in) prices.",
         intro="""<p>Pay and tax questions are the most common money searches, and the arithmetic is
usually simple once the rates are right. The trick is knowing which rate applies: marginal tax
brackets, FICA, state rates and pre-tax deductions all behave differently.</p>
<p>The take-home estimator uses current US federal brackets and the standard deduction. It is a
planning estimate, not payroll software — check your actual payslip or a state-specific calculator
for an exact figure.</p>"""),
    dict(id="health", name="Health", title="Health Calculators — BMI, BMR, TDEE and Body Fat",
         desc="BMI, basal metabolic rate, daily calorie needs, US Navy body fat, ideal weight "
              "range, pregnancy due date and ovulation estimates.",
         lede="Estimate the numbers behind fitness and health questions: BMI, calories burned at "
              "rest, daily calorie needs, body-fat percentage and pregnancy dates.",
         intro="""<p>Health calculators are screening and planning tools, not diagnoses. BMI, BMR and
TDEE are estimates built from population averages, and individual bodies vary.</p>
<p>Use the results to spot trends and set rough targets; for decisions about treatment, medication
or a medical condition, speak to a clinician.</p>"""),
    dict(id="dates", name="Dates & Time", title="Date Calculators — Age, Countdown and Business Days",
         desc="Exact age, date difference, countdown days, business days and time duration "
              "calculators with overnight and leap-year handling.",
         lede="Work out exact ages, days between dates, countdowns and hours worked — with correct "
              "handling of leap years, weekends and shifts that cross midnight.",
         intro="""<p>Date arithmetic is trickier than it looks: leap years, varying month lengths and
weekend-skipping rules all change the answer. These calculators do calendar arithmetic properly
rather than assuming 365 days or 30-day months.</p>
<p>Business-day calculations skip weekends but not public holidays — subtract those separately for
legal or contractual deadlines.</p>"""),
    dict(id="conversions", name="Conversions", title="Unit Converters and Practical Estimators",
         desc="Convert length, weight, temperature, speed, area and volume, and estimate fuel cost, "
              "electricity cost, paint and tile quantities.",
         lede="Convert units exactly and answer practical quantity questions: fuel for a trip, "
              "electricity for an appliance, paint for a room, tiles for a floor.",
         intro="""<p>These tools use exact unit definitions where they exist (the inch is exactly
2.54 cm, a US gallon exactly 3.785411784 L) and clearly stated assumptions where they do not
(coverage per gallon, real-world fuel economy).</p>
<p>For anything regulated — medication, freight, engineering — use the governing standard's figures
rather than these rounded results.</p>"""),
]

CAT_BY = {c["id"]: c for c in CATS}
CALCS = (calcs_loans.CALCS + calcs_investing.CALCS + calcs_salary.CALCS
         + calcs_health.CALCS + calcs_dates.CALCS + calcs_conv.CALCS
         + calcs_money2.CALCS + calcs_money3.CALCS)
BY = {c["slug"]: c for c in CALCS}
assert len(BY) == len(CALCS), "duplicate calculator slug"
# Sanitise cross-links: drop unknown slugs, then top up from the same category so every
# calculator always links to real siblings (the generator occasionally invented slugs).
for _c in CALCS:
    assert _c["cat"] in CAT_BY, f"{_c['slug']}: unknown category {_c['cat']}"
    _valid = [r for r in _c["related"] if r in BY and r != _c["slug"]]
    if len(_valid) < 3:
        for _sib in CALCS:
            if _sib["cat"] == _c["cat"] and _sib["slug"] not in _valid and _sib["slug"] != _c["slug"]:
                _valid.append(_sib["slug"])
            if len(_valid) >= 4:
                break
    _c["related"] = _valid[:4]
