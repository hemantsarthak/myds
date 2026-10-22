#!/usr/bin/env python3
"""Salary & tax calculators: hourly/salary conversion, overtime, take-home estimate,
raise, tip split, sales tax, discount, VAT, GST."""
from core import calc, num, sel, fnum

MONEY = "USD"

# 2025 US federal single/joint brackets (taxable income upper bound, marginal rate)
US_SINGLE = [(11925, .10), (48475, .12), (103350, .22), (197300, .24),
             (250525, .32), (626350, .35), (float("inf"), .37)]
US_MARRIED = [(23850, .10), (96950, .12), (206700, .22), (394600, .24),
              (501050, .32), (751600, .35), (float("inf"), .37)]
STANDARD_DEDUCTION = {"single": 15000.0, "married": 30000.0}
SS_WAGE_BASE = 176100.0


def _fed_tax(taxable, brackets):
    tax, prev = 0.0, 0.0
    for cap, rate in brackets:
        if taxable <= prev:
            break
        tax += (min(taxable, cap) - prev) * rate
        prev = cap
    return tax


# ---------------------------------------------------------------------------
# 1. hourly to salary
def _h2s_py(v):
    hourly = float(v["hourly"])
    hours = float(v["hours"])
    weeks = float(v["weeks"])
    annual = hourly * hours * weeks
    return {"annual": annual, "monthly": annual / 12, "weekly": hourly * hours,
            "daily": hourly * 8, "hours": hours * weeks}


HOURLY_TO_SALARY = calc(
    slug="hourly-to-salary", name="Hourly to Salary Calculator", cat="salary",
    title="Hourly to Salary Calculator — Annual, Monthly & Weekly Pay",
    desc="Convert an hourly wage into annual, monthly, weekly and daily salary using your real "
         "weekly hours and weeks worked per year.",
    h1="Hourly to salary calculator",
    lede="Turn an hourly rate into an annual salary — and monthly, weekly and daily figures — using "
         "your actual hours and how many weeks a year you are paid for.",
    fields=[num("hourly", "Hourly rate", 25, unit="USD / hr", pre="$", mn=0, mx=10000, step="0.25"),
            num("hours", "Hours per week", 40, unit="hours", mn=0, mx=100, step=0.5),
            num("weeks", "Paid weeks per year", 52, unit="weeks", mn=1, mx=52, step=1)],
    outs=[("annual", "Annual salary", "money0"), ("monthly", "Monthly pay", "money"),
          ("weekly", "Weekly pay", "money"), ("daily", "Daily pay (8 hr)", "money")],
    js="""
var annual=v.hourly*v.hours*v.weeks;
return {annual:annual,monthly:annual/12,weekly:v.hourly*v.hours,daily:v.hourly*8,
        hours:v.hours*v.weeks};
""",
    py=_h2s_py,
    how="""<p>An hourly wage becomes an annual salary by multiplying three numbers: the rate, the hours
worked each week and the weeks paid each year. The third number is where most estimates go wrong.
A full-time employee is normally paid for 52 weeks, including paid holiday and vacation, so
hourly × 40 × 52 is right for a salaried comparison. A contractor or part-year worker is paid only
for the weeks actually worked.</p>
<p>The calculator uses 8 hours for the daily figure. Overtime is not included — if you regularly
work extra hours, use the overtime calculator to value them properly. The monthly figure is simply
annual ÷ 12, which matches how salaried pay is usually spread, even though months have different
numbers of working days.</p>""",
    formula="""<p>Annual salary = hourly rate × hours per week × paid weeks per year. The other
figures follow from it:</p>
<div class="fml"><code>annual  = rate · hours/week · weeks/year
monthly = annual / 12
weekly  = rate · hours/week
daily   = rate · 8</code></div>
<p>Total paid hours are <em>hours/week × weeks/year</em>; at 40 hours and 52 weeks that is 2,080
hours a year, the standard full-time equivalent used by employers and lenders.</p>""",
    example="At {hourly} an hour for {hours} hours a week over {weeks} paid weeks, the annual salary "
            "is {annual}. That is {monthly} a month, {weekly} a week and {daily} a day for an "
            "eight-hour shift.",
    mistakes=[
        "<strong>Using 52 weeks but no paid leave.</strong> If you are paid only for weeks worked, "
        "set the weeks field to 50 or 48; leaving it at 52 overstates annual pay.",
        "<strong>Forgetting unpaid breaks.</strong> An eight-hour shift with a 30-minute unpaid "
        "break is 7.5 paid hours, not 8.",
        "<strong>Comparing hourly rates to salaries without benefits.</strong> A salaried package "
        "may include health insurance, retirement match and paid leave worth 20–30% of base pay.",
    ],
    faq=[
        ("How do I convert an hourly wage to an annual salary?",
         "Multiply the hourly rate by the number of paid hours per week, then by the number of paid "
         "weeks per year. For a standard full-time job that is rate × 40 × 52."),
        ("Is $25 an hour a good salary?",
         "At 40 hours a week for 52 weeks, $25 an hour is $52,000 a year before tax. Whether that is "
         "good depends on where you live and your household size; compare it with local median "
         "income rather than national figures."),
        ("Does annual salary include overtime?",
         "No. Salaried employment usually does not pay overtime, and this calculator does not include "
         "it for hourly work. Use the overtime calculator to add extra hours at the correct "
         "multiplier."),
    ],
    related=["salary-to-hourly", "overtime-pay", "paycheck-net", "raise-calculator"],
    note="Gross pay before tax. Unpaid breaks, overtime and unpaid leave are not included.",
)


# ---------------------------------------------------------------------------
# 2. salary to hourly
def _s2h_py(v):
    annual = float(v["annual"])
    hours = float(v["hours"])
    weeks = float(v["weeks"])
    total_hours = hours * weeks
    return {"hourly": annual / total_hours if total_hours else 0.0,
            "monthly": annual / 12, "weekly": annual / weeks if weeks else 0.0,
            "total_hours": total_hours}


SALARY_TO_HOURLY = calc(
    slug="salary-to-hourly", name="Salary to Hourly Calculator", cat="salary",
    title="Salary to Hourly Calculator — What Is My Time Worth",
    desc="Convert an annual salary into an hourly, weekly and monthly rate based on your real "
         "working hours and paid weeks. Useful for freelancing and overtime decisions.",
    h1="Salary to hourly calculator",
    lede="Turn an annual salary into an hourly rate using the hours you actually work — a useful "
         "number when comparing a job offer, freelancing or overtime.",
    fields=[num("annual", "Annual salary", 62400, unit=MONEY, pre="$", mn=0, mx=10000000, step=1000),
            num("hours", "Hours per week", 40, unit="hours", mn=1, mx=100, step=0.5),
            num("weeks", "Paid weeks per year", 52, unit="weeks", mn=1, mx=52, step=1)],
    outs=[("hourly", "Effective hourly rate", "money"), ("weekly", "Weekly pay", "money"),
          ("monthly", "Monthly pay", "money"), ("total_hours", "Paid hours per year", "int")],
    js="""
var totalH=v.hours*v.weeks;
return {hourly:totalH?v.annual/totalH:0,monthly:v.annual/12,
        weekly:v.weeks?v.annual/v.weeks:0,total_hours:totalH};
""",
    py=_s2h_py,
    how="""<p>Divide the salary by the number of paid hours in a year and you get the rate the job
actually pays per hour. For a standard US full-time role that is 40 × 52 = 2,080 hours, so a
$62,400 salary works out at $30 an hour. Change the weeks field if the job has long unpaid breaks,
term-time working or unpaid leave — the effective hourly rate rises as the paid hours fall.</p>
<p>The number is a comparison tool, not a statement that the job is hourly. It is especially useful
for two decisions: judging whether a salaried offer beats an hourly one once unpaid overtime is
counted, and setting a freelance rate. Freelancers should charge substantially more than their
salaried equivalent because they pay their own tax, benefits, holidays and downtime — commonly
1.3–1.5× the effective hourly rate.</p>""",
    formula="""<p>Paid hours per year = hours per week × paid weeks. Then:</p>
<div class="fml"><code>hourly  = annual salary / (hours/week · weeks/year)
weekly  = annual salary / weeks/year
monthly = annual salary / 12</code></div>
<p>At 40 hours and 52 weeks the divisor is 2,080. At 37.5 hours it is 1,950; at 35 hours it is
1,820.</p>""",
    example="A {annual} salary over {hours} hours a week for {weeks} weeks is {total_hours} paid "
            "hours a year, which works out at {hourly} an hour. That is {weekly} a week and "
            "{monthly} a month before tax.",
    mistakes=[
        "<strong>Ignoring unpaid overtime.</strong> If the job expects 45 hours for a 40-hour "
        "salary, the true hourly rate is lower. Enter the actual hours.",
        "<strong>Using the rate directly for freelance pricing.</strong> Self-employment tax, "
        "benefits, holidays and non-billable admin mean a freelancer needs far more per billable "
        "hour than the salaried equivalent.",
        "<strong>Forgetting that paid weeks vary.</strong> Teachers and term-time workers are often "
        "paid over 12 months for fewer working weeks — use the weeks actually worked for an "
        "effective rate, but the weeks paid for the monthly cash-flow view."
    ],
    faq=[
        ("What is $62,400 a year per hour?",
         "At 40 hours a week and 52 paid weeks, $62,400 a year is $30 an hour. The exact figure "
         "depends on paid hours: with 45 hours a week it drops to about $26.67."),
        ("Should I use 2,080 hours for a full-time year?",
         "Yes for a standard US full-time schedule: 40 hours × 52 weeks. Seasonal or part-time work "
         "should use the actual paid hours."),
        ("How do I compare a salary offer with an hourly job?",
         "Convert both to the same basis: annual gross pay. Add the value of benefits (health "
         "insurance, retirement match, paid leave) on the salary side, and subtract unpaid downtime "
         "and self-employment costs on the hourly side."),
    ],
    related=["hourly-to-salary", "overtime-pay", "paycheck-net", "raise-calculator"],
    note="Gross pay before tax. Benefits, bonuses and unpaid overtime are not included.",
)


# ---------------------------------------------------------------------------
# 3. overtime
def _ot_py(v):
    rate = float(v["rate"])
    reg_h = float(v["regular_hours"])
    ot_h = float(v["ot_hours"])
    mult = float(v["multiplier"])
    reg = rate * reg_h
    ot = rate * mult * ot_h
    return {"total": reg + ot, "overtime": ot, "regular": reg, "ot_rate": rate * mult}


OVERTIME = calc(
    slug="overtime-pay", name="Overtime Pay Calculator", cat="salary",
    title="Overtime Pay Calculator — Time and a Half & Weekly Pay",
    desc="Calculate overtime pay at time and a half or any multiplier, plus regular pay and total "
         "weekly gross pay from your hourly rate.",
    h1="Overtime pay calculator",
    lede="Enter your hourly rate, regular hours, overtime hours and multiplier to see weekly gross "
         "pay broken into regular and overtime earnings.",
    fields=[num("rate", "Hourly rate", 20, unit="USD / hr", pre="$", mn=0, mx=10000, step="0.25"),
            num("regular_hours", "Regular hours", 40, unit="hours", mn=0, mx=168, step=0.5),
            num("ot_hours", "Overtime hours", 10, unit="hours", mn=0, mx=100, step=0.5),
            num("multiplier", "Overtime multiplier", 1.5, unit="×", mn=1, mx=3, step="0.1")],
    outs=[("total", "Total gross pay", "money"), ("overtime", "Overtime pay", "money"),
          ("regular", "Regular pay", "money"), ("ot_rate", "Overtime hourly rate", "money")],
    viz=[("Regular", "regular", "money"), ("Overtime", "overtime", "money")],
    js="""
var reg=v.rate*v.regular_hours, ot=v.rate*v.multiplier*v.ot_hours;
return {total:reg+ot,overtime:ot,regular:reg,ot_rate:v.rate*v.multiplier};
""",
    py=_ot_py,
    how="""<p>In the US, the Fair Labor Standards Act requires covered employers to pay non-exempt
employees 1.5 times their regular rate for hours worked beyond 40 in a workweek. So a $20 hourly
rate becomes an overtime rate of $30, and 10 overtime hours add $300 to the week's pay. Overtime is
generally based on the regular rate, which can include non-discretionary bonuses and shift
differentials — not just the base hourly wage.</p>
<p>The multiplier is editable because rules differ: some union agreements, public-sector contracts
and holiday policies pay double time, and a few pay 1.25×. The calculation here is weekly gross pay
before tax; it assumes the overtime hours are all paid at the chosen multiplier. State rules can
differ from federal ones — California, for example, requires overtime after 8 hours in a day as well
as over 40 in a week.</p>""",
    formula="""<p>Regular pay = hourly rate × regular hours. Overtime pay = hourly rate × multiplier ×
overtime hours. Total gross pay is their sum:</p>
<div class="fml"><code>regular  = rate · regular hours
overtime = rate · multiplier · overtime hours
total    = regular + overtime</code></div>
<p>At the federal US default of 1.5×, the overtime hourly rate is one and a half times the regular
rate.</p>""",
    example="At {rate} an hour with {regular_hours} regular hours and {ot_hours} overtime hours at "
            "{multiplier}×, regular pay is {regular}, overtime pay is {overtime}, and total gross pay "
            "is {total} for the week.",
    mistakes=[
        "<strong>Only counting hours over 40 in a week.</strong> Some states and contracts require "
        "daily overtime. Check local rules before relying on the federal rule.",
        "<strong>Using the wrong base rate.</strong> Bonuses and shift differentials may increase "
        "the regular rate used for overtime, which raises the overtime pay.",
        "<strong>Forgetting tax on overtime.</strong> Overtime is taxed like ordinary income. A "
        "higher-gross week can push part of the pay into a higher marginal bracket."
    ],
    faq=[
        ("What is time and a half?",
         "Time and a half means 1.5 times your regular hourly rate for overtime hours — the US "
         "federal requirement for non-exempt employees after 40 hours in a workweek."),
        ("Are salaried employees entitled to overtime?",
         "Not usually. US federal rules exempt salaried employees who meet the duties and salary "
         "threshold tests, but many states have stricter tests, and a salaried worker earning below "
         "the threshold may still be entitled to overtime."),
        ("Is overtime paid weekly or per pay period?",
         "Overtime is calculated per workweek under federal law, even if you are paid every two "
         "weeks. A 50-hour week followed by a 30-hour week does not average out to 40."),
    ],
    related=["hourly-to-salary", "salary-to-hourly", "paycheck-net", "tip-split"],
    note="Weekly gross pay; taxes are not deducted. Overtime rules vary by state and contract.",
)


# ---------------------------------------------------------------------------
# 4. paycheck net estimate
def _paycheck_py(v):
    gross = float(v["salary"])
    k401 = min(max(float(v["k401"]), 0.0), 100.0) / 100 * gross
    state_rate = min(max(float(v["state_rate"]), 0.0), 20.0) / 100
    brackets = US_MARRIED if v["filing"] == "married" else US_SINGLE
    deduction = STANDARD_DEDUCTION["married" if v["filing"] == "married" else "single"]
    taxable = max(0.0, gross - k401 - deduction)
    fed = _fed_tax(taxable, brackets)
    ss = min(gross, SS_WAGE_BASE) * 0.062
    medicare = gross * 0.0145
    state = (gross - k401) * state_rate
    net = gross - k401 - fed - ss - medicare - state
    return {"monthly": net / 12, "net": net, "fed": fed, "fica": ss + medicare, "state": state,
            "k401": k401}


PAYCHECK = calc(
    slug="paycheck-net-estimate", name="Paycheck Net Estimate Calculator", cat="salary",
    title="Paycheck Net Estimate Calculator — Take-Home Pay After Tax",
    desc="Estimate US take-home pay from a gross salary using 2025 federal brackets, FICA, state "
         "tax and pre-tax 401(k) contributions. See annual and monthly net pay.",
    h1="Paycheck net estimate calculator",
    lede="Estimate annual and monthly take-home pay from a gross salary, using the standard "
         "deduction, federal brackets, FICA and a state-tax rate you control.",
    fields=[num("salary", "Gross annual salary", 80000, unit=MONEY, pre="$", mn=0, mx=5000000, step=1000),
            sel("filing", "Filing status",
                [("single", "Single"), ("married", "Married filing jointly")], "single"),
            num("k401", "Pre-tax 401(k) contribution", 6, unit="% of salary", mn=0, mx=100, step="0.5"),
            num("state_rate", "State income tax rate", 0, unit="%", mn=0, mx=20, step="0.1")],
    outs=[("monthly", "Estimated monthly take-home", "money"),
          ("net", "Annual take-home", "money0"),
          ("fed", "Federal income tax", "money0"),
          ("fica", "FICA (Social Security + Medicare)", "money0"),
          ("state", "State income tax", "money0")],
    js="""
var married = v.filing === 'married';
var brackets = married
  ? [[23850,.10],[96950,.12],[206700,.22],[394600,.24],[501050,.32],[751600,.35],[Infinity,.37]]
  : [[11925,.10],[48475,.12],[103350,.22],[197300,.24],[250525,.32],[626350,.35],[Infinity,.37]];
var deduction = married ? 30000 : 15000;
var gross = v.salary, k = gross * v.k401 / 100;
var taxable = Math.max(0, gross - k - deduction), fed = 0, prev = 0;
for (var i = 0; i < brackets.length; i++) {
  var cap = brackets[i][0], rate = brackets[i][1];
  if (taxable <= prev) break;
  fed += (Math.min(taxable, cap) - prev) * rate;
  prev = cap;
}
var ss = Math.min(gross, 176100) * 0.062, med = gross * 0.0145;
var state = (gross - k) * v.state_rate / 100;
var net = gross - k - fed - ss - med - state;
return {monthly: net/12, net: net, fed: fed, fica: ss+med, state: state, k401: k};
""",
    py=_paycheck_py,
    how="""<p>This is a planning estimate, not a payroll system. It starts with gross salary,
subtracts pre-tax 401(k) contributions, applies the 2025 standard deduction for the chosen filing
status, runs the result through the 2025 federal marginal brackets, adds FICA (6.2% Social
Security up to the wage base, 1.45% Medicare on all wages), and applies the state rate you enter.</p>
<p>It deliberately leaves out the details that vary person to person: itemised deductions, tax
credits (especially the child tax credit), HSA and dependent-care accounts, local taxes, wage
garnishments, the additional 0.9% Medicare tax on high earners, and state-specific rules. That
means the answer is typically within a few percent of a real paycheck for a simple single or
married filer taking only the standard deduction, and can be off by more for complex situations.
Use it to understand the size of the gap between gross and net, then check a payroll calculator
that knows your state for an exact figure.</p>""",
    formula="""<p>Taxable income = gross − pre-tax 401(k) − standard deduction. Federal tax is the sum
of marginal slices:</p>
<div class="fml"><code>fed tax = Σ (min(taxable, bracket top) − previous top) × rate
FICA = min(gross, 176,100) × 6.2% + gross × 1.45%
net = gross − 401(k) − fed tax − FICA − state tax</code></div>
<p>State tax here is a flat rate applied to (gross − 401k); real state schedules are progressive
or exempt certain income.</p>""",
    example="On a {salary} salary, filing {filing}, contributing {k401}% to a pre-tax 401(k) and "
            "paying {state_rate}% state tax, take-home is about {monthly} a month ({net} a year). "
            "Federal income tax is {fed}, FICA is {fica} and state tax is {state}.",
    mistakes=[
        "<strong>Treating the estimate as exact.</strong> Credits, itemised deductions, local taxes "
        "and payroll deductions (health insurance, HSA) all move the final number.",
        "<strong>Forgetting that 401(k) lowers income tax but not FICA.</strong> Pre-tax "
        "contributions reduce taxable income for income tax, while Social Security and Medicare are "
        "still charged on the contribution.",
        "<strong>Assuming a raise is worth its full amount.</strong> Moving into a higher bracket "
        "only taxes the extra income at the higher rate — but benefits phase-outs can make the "
        "effective marginal cost higher than the bracket suggests."
    ],
    faq=[
        ("Why is my take-home pay lower than this estimate?",
         "Common reasons are state and local taxes, health insurance premiums, HSA or FSA "
         "contributions, wage garnishments and tax credits you were expecting but which are not "
         "modelled here. The estimate assumes only the standard deduction."),
        ("How much tax is taken out of a paycheck?",
         "In the US, federal income tax withholding depends on your W-4, plus FICA at 7.65% for most "
         "employees (6.2% Social Security + 1.45% Medicare), plus state tax if your state has an "
         "income tax."),
        ("Is this using current tax brackets?",
         "It uses the 2025 federal brackets and standard deduction. Tax rules change most years, so "
         "check the IRS figures for the tax year you are planning."),
    ],
    related=["hourly-to-salary", "salary-to-hourly", "overtime-pay", "raise-calculator"],
    note="Estimate only: 2025 US federal brackets, standard deduction, no credits or itemised deductions.",
)


# ---------------------------------------------------------------------------
# 5. raise calculator
def _raise_py(v):
    salary = float(v["salary"])
    pct = float(v["raise_pct"])
    new = salary * (1 + pct / 100)
    return {"new_salary": new, "increase": new - salary, "new_monthly": new / 12,
            "old_monthly": salary / 12}


RAISE = calc(
    slug="raise-calculator", name="Raise Calculator", cat="salary",
    title="Raise Calculator — New Salary After a Percentage Increase",
    desc="Work out your new salary after a percentage raise, the annual increase and the extra "
         "money per month and per paycheck.",
    h1="Raise calculator",
    lede="Enter your current salary and the raise percentage to see the new salary, the annual "
         "increase in dollars and what it adds to each month.",
    fields=[num("salary", "Current annual salary", 52000, unit=MONEY, pre="$", mn=0, mx=10000000, step=1000),
            num("raise_pct", "Raise", 5, unit="%", mn=0, mx=200, step="0.1")],
    outs=[("new_salary", "New annual salary", "money0"), ("increase", "Annual increase", "money"),
          ("new_monthly", "New monthly pay", "money"), ("old_monthly", "Current monthly pay", "money")],
    js="""
var now=v.salary, neu=now*(1+v.raise_pct/100);
return {new_salary:neu,increase:neu-now,new_monthly:neu/12,old_monthly:now/12};
""",
    py=_raise_py,
    how="""<p>A percentage raise is calculated on the current annual salary: multiply it by the raise
percentage and add the result. A 5% raise on $52,000 is $2,600 a year, taking the salary to
$54,600, or about $217 more a month before tax.</p>
<p>Two things are worth knowing when you negotiate. First, a raise compounds: the next percentage
increase applies to the new, higher base, so earlier raises are worth more over a career than later
ones of the same size. Second, the spending value of a raise is reduced by tax and by inflation. If
prices rose 3% and your raise was 3%, you have held your position, not improved it — and moving into
a higher tax bracket means the take-home increase is smaller than the gross increase.</p>""",
    formula="""<p>New salary = current salary × (1 + raise% ÷ 100). The annual increase is the
difference, and the monthly figures divide by 12:</p>
<div class="fml"><code>new salary = salary · (1 + r)
increase   = salary · r
new monthly = new salary / 12</code></div>
<p>For a pay cut, enter a negative percentage — the same formula applies.</p>""",
    example="A {raise_pct}% raise on {salary} takes the salary to {new_salary}, an increase of "
            "{increase} a year. Monthly pay rises from {old_monthly} to {new_monthly} before tax.",
    mistakes=[
        "<strong>Confusing the raise with the new salary.</strong> 5% is the increase, not the new "
        "figure. The new salary is 105% of the old one.",
        "<strong>Ignoring tax.</strong> If the raise moves income into a higher bracket only the "
        "extra income is taxed at that rate, but the take-home gain is still smaller than the gross "
        "increase.",
        "<strong>Not adjusting for inflation.</strong> A raise below the inflation rate is a pay cut "
        "in real terms; check the inflation calculator when the number feels small.",
    ],
    faq=[
        ("How do I calculate a 5% raise?",
         "Multiply the current salary by 0.05 to get the increase, then add it: $52,000 × 0.05 = "
         "$2,600, so the new salary is $54,600."),
        ("Is a 3% raise good?",
         "3% is a common annual cost-of-living adjustment. Whether it is good depends on inflation "
         "and your performance: a raise at or below inflation keeps real pay flat, so many "
         "negotiators target above-inflation increases."),
        ("How do I ask for a raise?",
         "Bring evidence of market pay for your role, a record of results and the added scope you "
         "have taken on. Ask for a specific number rather than a range, and be ready to discuss "
         "total compensation, not just base salary."),
    ],
    related=["hourly-to-salary", "salary-to-hourly", "paycheck-net", "inflation-calculator"],
    note="Gross pay before tax. Bonuses, equity and benefits are not included.",
)


# ---------------------------------------------------------------------------
# 6. tip and split
def _tip_py(v):
    bill = float(v["bill"])
    pct = float(v["tip"])
    people = max(1, int(round(float(v["people"]))))
    tip = bill * pct / 100
    total = bill + tip
    return {"tip": tip, "total": total, "per_person": total / people, "tip_per_person": tip / people}


TIP = calc(
    slug="tip-split", name="Tip & Bill Split Calculator", cat="salary",
    title="Tip Calculator — Tip Amount and Split the Bill",
    desc="Calculate the tip on a bill, the total and how much each person owes when splitting "
         "between friends. Works for restaurants, taxis and delivery.",
    h1="Tip and bill split calculator",
    lede="Enter the bill, the tip percentage and how many people are splitting it to get the tip, "
         "the total and each person's share.",
    fields=[num("bill", "Bill amount", 80, unit=MONEY, pre="$", mn=0, mx=100000, step="0.01"),
            num("tip", "Tip percentage", 18, unit="%", mn=0, mx=100, step=1),
            num("people", "Split between", 4, unit="people", mn=1, mx=100, step=1)],
    outs=[("per_person", "Each person pays", "money"), ("tip", "Tip amount", "money"),
          ("total", "Total bill", "money"), ("tip_per_person", "Tip per person", "money")],
    js="""
var tip=v.bill*v.tip/100, total=v.bill+tip, p=Math.max(1,Math.round(v.people));
return {tip:tip,total:total,per_person:total/p,tip_per_person:tip/p};
""",
    py=_tip_py,
    how="""<p>Tipping is a percentage of the pre-tax bill in most US situations, although restaurant
point-of-sale systems often calculate it on the total and diners frequently do too. The convention:
15–20% for table service, around 10% for counter service if there is a tip jar, 15–20% for taxis and
ride-hailing, and 15–20% for food delivery. Some states now allow tipped workers to be paid a lower
cash wage with tips making up the difference, which is why tipping customs feel uneven.</p>
<p>The split is the simple part: divide the total by the number of people. If you want to split the
bill but tip separately, use the “tip per person” line. When the bill includes a mandatory service
charge, that charge is part of the total and should not normally be tipped on again — check the
receipt before adding 20% on top.</p>""",
    formula="""<p>Tip = bill × tip% ÷ 100. Total = bill + tip. Each person pays total ÷ number of
people:</p>
<div class="fml"><code>tip   = bill · pct / 100
total = bill + tip
share = total / people</code></div>
<p>To tip on the pre-tax amount instead, use the pre-tax bill in the calculation.</p>""",
    example="An {bill} bill with an {tip}% tip adds {tip} for a total of {total}. Split between "
            "{people} people, each person pays {per_person} — of which {tip_per_person} is their "
            "share of the tip.",
    mistakes=[
        "<strong>Rounding the split down.</strong> Dividing $94.40 between four people gives $23.60 "
        "each; rounding to $23 leaves a gap. Round each share up if you are covering the bill.",
        "<strong>Tipping on top of a service charge.</strong> A mandatory 18% service charge is "
        "usually the tip. Check whether the receipt says “service charge” or “gratuity”.",
        "<strong>Using the tax-inclusive total for the percentage.</strong> In high-tax cities this "
        "can add a full percentage point to the tip. Tip on the pre-tax subtotal if you want the "
        "customary amount."
    ],
    faq=[
        ("How much should I tip at a restaurant?",
         "In the US, 15–20% of the pre-tax bill is the standard range for table service, with 20% "
         "common for good service. Buffets and counter service usually take less."),
        ("How do I split a bill unevenly?",
         "Calculate each person's own items and tip on their subtotal; this calculator splits the "
         "whole bill equally. For mixed groups, equal splitting plus a note about who ordered drinks "
         "is usually the simplest."),
        ("Is the tip calculated before or after tax?",
         "Custom is to tip on the pre-tax subtotal. Both are accepted; using the pre-tax amount "
         "gives a slightly lower tip that is still within normal range."),
    ],
    related=["sales-tax", "discount-percent-off", "paycheck-net", "hourly-to-salary"],
    note="Assumes an equal split and no service charge already included.",
)


# ---------------------------------------------------------------------------
# 7. sales tax
def _salestax_py(v):
    price = float(v["price"])
    rate = float(v["rate"])
    tax = price * rate / 100
    return {"tax": tax, "total": price + tax, "price": price, "effective": rate}


SALES_TAX = calc(
    slug="sales-tax", name="Sales Tax Calculator", cat="salary",
    title="Sales Tax Calculator — Tax Amount and Total Price",
    desc="Add US sales tax to a price, or work out how much tax is inside a tax-inclusive total. "
         "See the tax amount, total and effective rate.",
    h1="Sales tax calculator",
    lede="Calculate the sales tax on a purchase, the total with tax, and the pre-tax price if you "
         "only know the final amount.",
    fields=[num("price", "Price before tax", 100, unit=MONEY, pre="$", mn=0, mx=10000000, step="0.01"),
            num("rate", "Sales tax rate", 8.25, unit="%", mn=0, mx=30, step="0.01")],
    outs=[("tax", "Sales tax", "money"), ("total", "Total price", "money"),
          ("effective", "Combined effective rate", "pct")],
    js="""
var p=v.price, r=v.rate/100;
return {tax:p*r,total:p*(1+r),effective:v.rate};
""",
    py=_salestax_py,
    how="""<p>US sales tax is charged at the point of sale and is a percentage of the selling price.
It is set by state, county and city governments, so the combined rate at one address can combine
three or more layers: state, county, city and sometimes special district taxes. Five states have no
statewide sales tax, and rates range from around 1.8% to over 11% in some cities.</p>
<p>Two practical uses for this calculator. First, working out what a purchase will actually cost
after tax — add the local combined rate. Second, reverse-engineering the pre-tax price from a
receipt total, which is handy for expense claims and budgeting, especially for items like groceries
and prescription drugs that are often exempt. If an item is tax-exempt or taxed at a reduced rate
in your area, use the effective rate that applies to that item rather than the general rate.</p>""",
    formula="""<p>Tax = price × rate ÷ 100; total = price + tax. To go backwards from a
tax-inclusive total <em>T</em> at rate <em>r</em>:</p>
<div class="fml"><code>tax   = price · r
total = price · (1 + r)
price = total / (1 + r)</code></div>
<p>For example, a $108.25 total at 8.25% implies a pre-tax price of $100 and $8.25 of tax.</p>""",
    example="A {price} purchase at a {rate}% combined sales-tax rate adds {tax} of tax, for a total "
            "of {total}. The effective combined rate on the purchase is {effective}.",
    mistakes=[
        "<strong>Using a state rate instead of the combined rate.</strong> The rate that applies at "
        "the register includes county and city taxes; look up the address-specific rate.",
        "<strong>Charging tax on exempt items.</strong> Many states exempt food, prescription drugs "
        "and some services. Tax-exempt purchases should use a 0% rate.",
        "<strong>Forgetting online marketplace rules.</strong> Marketplaces such as Amazon collect "
        "sales tax based on the delivery address, not the seller's home state."
    ],
    faq=[
        ("How do I calculate sales tax backwards?",
         "Divide the tax-inclusive price by 1 + (rate ÷ 100). A $108.25 total at 8.25% becomes "
         "$100.00 before tax; the difference is the tax."),
        ("Which US states have no sales tax?",
         "Alaska, Delaware, Montana, New Hampshire and Oregon have no statewide sales tax, though "
         "local taxes may apply in parts of Alaska and Montana."),
        ("Is sales tax the same as VAT?",
         "No. Sales tax is collected once, at the final sale to the consumer. VAT and GST are "
         "collected at multiple stages along the supply chain with credits for tax already paid."),
    ],
    related=["vat-calculator", "gst-calculator", "discount-percent-off", "tip-split"],
    note="US-style single-stage sales tax. Local rates and item exemptions vary.",
)


# ---------------------------------------------------------------------------
# 8. discount / percent off
def _discount_py(v):
    price = float(v["price"])
    pct = float(v["discount"])
    tax_rate = float(v["tax"])
    saved = price * pct / 100
    final = price - saved
    tax = final * tax_rate / 100
    return {"final": final, "saved": saved, "tax": tax, "total": final + tax}


DISCOUNT = calc(
    slug="discount-percent-off", name="Discount Calculator", cat="salary",
    title="Discount Calculator — Percent Off and Final Price",
    desc="Calculate a percentage discount, the money saved and the final price — with optional "
         "sales tax on top. Includes stacked discounts.",
    h1="Percent-off discount calculator",
    lede="Work out how much a discount saves, what the item costs after the reduction, and the "
         "total after tax.",
    fields=[num("price", "Original price", 200, unit=MONEY, pre="$", mn=0, mx=10000000, step="0.01"),
            num("discount", "Discount", 25, unit="% off", mn=0, mx=100, step="1"),
            num("tax", "Sales tax added after discount", 0, unit="%", mn=0, mx=30, step="0.01")],
    outs=[("final", "Price after discount", "money"), ("saved", "You save", "money"),
          ("total", "Total with tax", "money"), ("tax", "Tax added", "money")],
    js="""
var saved=v.price*v.discount/100, fin=v.price-saved, tax=fin*v.tax/100;
return {final:fin,saved:saved,tax:tax,total:fin+tax};
""",
    py=_discount_py,
    how="""<p>A percentage discount reduces the price by that share of the original: 25% off $200
saves $50 and leaves $150. Sales tax, where it applies, is charged on the discounted price rather
than the original price, which is why the order of operations matters.</p>
<p>Retail discounts are often stacked, and the arithmetic surprises people. Two successive 20%
discounts do not equal 40% off — they equal 36% off, because the second 20% applies to a price that
has already been reduced. To handle stacked discounts, apply them one after another, or enter the
equivalent single discount: <em>1 − (1 − d1)(1 − d2)</em>. Similarly, a “25% off, then an extra 10%”
is 32.5% total, not 35%.</p>""",
    formula="""<p>Discount = original price × discount% ÷ 100. Final price = original − discount.
With optional tax on the discounted price:</p>
<div class="fml"><code>saved   = price · d / 100
final   = price · (1 − d / 100)
total   = final · (1 + tax / 100)
stacked = 1 − (1 − d1)(1 − d2)</code></div>
<p>For a sale price and the discount, the implied original price is final ÷ (1 − d/100).</p>""",
    example="A {price} item at {discount}% off costs {final} after the discount — a saving of "
            "{saved}. With {tax}% sales tax added on the reduced price the total is {total}, "
            "including {tax} of tax.",
    mistakes=[
        "<strong>Adding stacked discounts.</strong> 20% plus 20% is 36% off, not 40%. Apply each "
        "discount to the already-reduced price.",
        "<strong>Adding the tax to the original price.</strong> Sales tax applies to what you "
        "actually pay after the discount.",
        "<strong>Assuming the ticket price is the reference price.</strong> Some retailers raise the "
        "original price before advertising a discount. Compare the final price with the market, not "
        "the crossed-out number.",
    ],
    faq=[
        ("How do I calculate 25% off?",
         "Multiply the price by 0.25 to get the saving, then subtract it: $200 × 0.25 = $50 saved, "
         "so the final price is $150. Alternatively multiply by 0.75."),
        ("What does an extra 20% off mean?",
         "The 20% applies to the already-discounted price, not the original price. Two 20% "
         "discounts compound to 36% off the original."),
        ("Is it cheaper to buy with a discount or with a coupon after tax?",
         "Compare the final out-of-pocket total. A percentage discount reduces the price and "
         "therefore the tax charged; a fixed-amount coupon reduces the price but may still be "
         "taxed differently depending on local rules."),
    ],
    related=["sales-tax", "tip-split", "vat-calculator", "gst-calculator"],
    note="Tax, where you add it, is applied to the discounted price.",
)


# ---------------------------------------------------------------------------
# 9. VAT
def _vat_py(v):
    amount = float(v["amount"])
    rate = float(v["rate"])
    included = v["mode"] == "included"
    if included:
        net = amount / (1 + rate / 100)
        vat = amount - net
        gross = amount
    else:
        net = amount
        vat = amount * rate / 100
        gross = amount + vat
    return {"vat": vat, "net": net, "gross": gross}


VAT = calc(
    slug="vat-calculator", name="VAT Calculator", cat="salary",
    title="VAT Calculator — Add or Remove VAT",
    desc="Add VAT to a net price or extract the VAT from a VAT-inclusive amount. See the net, VAT "
         "and gross figures at any standard or reduced rate.",
    h1="VAT calculator",
    lede="Add VAT to a price, or take it back out of a VAT-inclusive total, at any rate — with the "
         "net, VAT and gross amounts shown separately.",
    fields=[num("amount", "Amount", 120, unit="", pre="$", mn=0, mx=10000000, step="0.01"),
            num("rate", "VAT rate", 20, unit="%", mn=0, mx=50, step="0.1"),
            sel("mode", "Amount entered is",
                [("included", "VAT-inclusive (gross)"), ("excluded", "Before VAT (net)")], "included")],
    outs=[("vat", "VAT amount", "money"), ("net", "Net amount", "money"),
          ("gross", "Gross amount", "money")],
    js="""
var a=v.amount, r=v.rate/100;
if (v.mode === 'included') { var net=a/(1+r); return {vat:a-net,net:net,gross:a}; }
var vat=a*r; return {vat:vat,net:a,gross:a+vat};
""",
    py=_vat_py,
    how="""<p>VAT is a consumption tax added at each stage of a supply chain, with businesses
reclaiming the VAT they paid on purchases. For a consumer, though, it behaves like a single tax on
the final price. The confusing part is that prices in the EU, UK and many other markets are quoted
VAT-inclusive, while business invoices are quoted net.</p>
<p>The two operations are not symmetric. Adding 20% VAT to a €100 net price gives €120 gross.
Extracting VAT from a €120 gross price does not mean subtracting 20% — that would give €96. The
correct operation is to divide by 1.20, giving €100 net and €20 VAT. Use the mode selector to tell
the calculator which direction you want. Standard rates vary widely: 20% in the UK, 19–21% across
most of the EU, 25% in Denmark and Sweden, and 5% or 0% for reduced categories such as food and
books.</p>""",
    formula="""<p>If the amount is net: VAT = net × rate ÷ 100, gross = net + VAT. If the amount is
gross, the net is found by dividing:</p>
<div class="fml"><code>net   = gross / (1 + rate / 100)
vat   = gross − net
gross = net · (1 + rate / 100)</code></div>
<p>The effective VAT fraction of a gross price is <em>rate ÷ (100 + rate)</em> — for 20% that is
1/6, not 1/5.</p>""",
    example="With the default amount entered as VAT-inclusive at {rate}%, {gross} breaks down into "
            "{net} net plus {vat} of VAT. Switching the mode to net-inclusive would add VAT to the "
            "amount instead.",
    mistakes=[
        "<strong>Subtracting the rate to remove VAT.</strong> Dividing €120 by 1.20 gives €100; "
        "subtracting 20% gives €96, which is wrong.",
        "<strong>Using the wrong rate.</strong> Reduced and zero-rated categories exist for food, "
        "books, children's clothing and more. Check the rate for the actual goods.",
        "<strong>Mixing net and gross when invoicing.</strong> Small businesses must show net, VAT "
        "and gross clearly on a VAT invoice; mixing them up creates bookkeeping errors."
    ],
    faq=[
        ("How do I calculate VAT from a gross amount?",
         "Divide the gross amount by 1 + (VAT rate ÷ 100). At 20%, €120 ÷ 1.20 = €100 net, so the "
         "VAT is €20."),
        ("What is the difference between VAT and sales tax?",
         "VAT is collected at each stage of the supply chain with credits for tax already paid; "
         "sales tax is collected only once, from the final consumer. Both are consumption taxes on "
         "the final price."),
        ("Which countries use VAT?",
         "Most of Europe, the UK, and many countries in Asia, Africa and South America use VAT. "
         "Australia, Canada, India and Singapore use a Goods and Services Tax, which works "
         "similarly."),
    ],
    related=["gst-calculator", "sales-tax", "discount-percent-off", "tip-split"],
    note="Single-rate VAT. Real schedules have reduced and zero rates for specific categories.",
)


# ---------------------------------------------------------------------------
# 10. GST
def _gst_py(v):
    amount = float(v["amount"])
    rate = float(v["rate"])
    included = v["mode"] == "included"
    if included:
        net = amount / (1 + rate / 100)
        gst = amount - net
        total = amount
    else:
        net = amount
        gst = amount * rate / 100
        total = amount + gst
    return {"gst": gst, "net": net, "total": total, "half": gst / 2}


GST = calc(
    slug="gst-calculator", name="GST Calculator", cat="salary",
    title="GST Calculator — Add or Remove Goods and Services Tax",
    desc="Calculate GST on a net price or extract it from a GST-inclusive total. Includes the "
         "CGST/SGST half split used on Indian invoices.",
    h1="GST calculator",
    lede="Add or remove Goods and Services Tax at any rate, with the net, GST and total shown "
         "separately and an even CGST/SGST split for Indian invoices.",
    fields=[num("amount", "Amount", 1000, unit="", pre="₹/$", mn=0, mx=10000000, step="0.01"),
            num("rate", "GST rate", 18, unit="%", mn=0, mx=50, step="0.1"),
            sel("mode", "Amount entered is",
                [("excluded", "Before GST (net)"), ("included", "GST-inclusive (total)")], "excluded")],
    outs=[("gst", "GST amount", "money"), ("net", "Net amount", "money"),
          ("total", "Total with GST", "money"), ("half", "CGST / SGST each (half)", "money")],
    js="""
var a=v.amount, r=v.rate/100;
if (v.mode === 'included') { var net=a/(1+r); return {gst:a-net,net:net,total:a,half:(a-net)/2}; }
var gst=a*r; return {gst:gst,net:a,total:a+gst,half:gst/2};
""",
    py=_gst_py,
    how="""<p>GST is a multi-stage consumption tax that works like VAT: each business in the supply
chain charges GST on its sale and claims credit for the GST it paid on its purchases, so the tax
ultimately lands on the final consumer once. It is used in India, Australia, Canada, New Zealand,
Singapore and many other countries, with very different rates and rules: 18% is a common Indian
slab, Australia's rate is 10%, and Canada's federal rate is 5% before provincial taxes.</p>
<p>In India, most intra-state sales split the GST evenly between central and state governments as
CGST and SGST, while inter-state sales attract a single IGST — which is why invoices show the two
halves. The half-split output here shows that even division; it is not a separate tax. This
calculator uses one rate for the whole amount; real invoices can mix rates when a basket contains
items from different slabs.</p>""",
    formula="""<p>If the amount is net: GST = net × rate ÷ 100. If the amount is GST-inclusive, the
net is <em>gross ÷ (1 + rate ÷ 100)</em> and the tax is the difference:</p>
<div class="fml"><code>gst   = net · r
total = net · (1 + r)
net   = total / (1 + r)
CGST = SGST = gst / 2</code></div>
<p>For a 18% GST, the tax fraction of a gross price is 18/118 ≈ 15.25%.</p>""",
    example="A {amount} amount before GST at {rate}% attracts {gst} of GST, for a total of {total}. "
            "On an Indian invoice that would typically be shown as {half} CGST and {half} SGST.",
    mistakes=[
        "<strong>Dividing the gross by 1 + rate as a decimal wrong way.</strong> At 18%, divide by "
        "1.18 — not by 0.18 and not by 1.018.",
        "<strong>Applying GST to tax-exempt items.</strong> Many countries exempt or zero-rate "
        "basic food, healthcare and education. Use the rate that applies to each line item.",
        "<strong>Mixing CGST/SGST and IGST.</strong> Intra-state sales split into CGST and SGST; "
        "inter-state sales use IGST. Do not charge both on the same invoice."
    ],
    faq=[
        ("How is GST calculated?",
         "GST is a percentage of the taxable value: net amount × rate ÷ 100. For a GST-inclusive "
         "figure, divide by 1 + (rate ÷ 100) to get the net value, and subtract for the tax."),
        ("What is the difference between GST and VAT?",
         "Economically they are the same kind of multi-stage consumption tax. The name differs by "
         "country, and the rules for registration, rates and credits differ."),
        ("What is CGST and SGST?",
         "In India, intra-state GST is split evenly between the central government (CGST) and the "
         "state government (SGST). Inter-state transactions use IGST instead."),
    ],
    related=["vat-calculator", "sales-tax", "discount-percent-off", "tip-split"],
    note="Single-rate GST. Mixed-rate baskets and state-specific rules are not modelled.",
)


CALCS = [HOURLY_TO_SALARY, SALARY_TO_HOURLY, OVERTIME, PAYCHECK, RAISE, TIP,
         SALES_TAX, DISCOUNT, VAT, GST]
