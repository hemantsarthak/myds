#!/usr/bin/env python3
"""Fourth wave of money calculators: dividend income, rent affordability, down payment and US
self-employment tax.

Every calculator has a Python implementation (server-rendered initial result) and a JavaScript twin
(live result) that must agree; see core.py for the field/output contract.
"""
import math

from core import calc, num, sel

MONEY = "USD"


DIVIDEND_INCOME = calc(
    slug="dividend-income-calculator", name="Dividend Income Calculator", cat="investing",
    title="Dividend Income Calculator — Annual and Monthly Dividend Income",
    desc="Work out the dividend income a shareholding produces: annual and monthly income, the "
         "dividend yield you bought at, and the capital needed to hit a target income.",
    h1="Dividend income calculator",
    lede="Enter the number of shares, the price you paid and the annual dividend per share to see the "
         "income it produces and the capital needed to reach a monthly target.",
    fields=[num("shares", "Number of shares", 500, unit="shares", mn=1, mx=10**7),
            num("price", "Purchase price per share", 40, unit=MONEY, mn=0.01, mx=10**7, step="0.01"),
            num("dividend", "Annual dividend per share", 2.4, unit=MONEY, mn=0, mx=10**4, step="0.01"),
            num("target", "Target monthly income", 500, unit=MONEY, mn=0, mx=10**6)],
    outs=[("invested", "Amount invested", "money0"), ("annual", "Annual dividend income", "money"),
          ("monthly", "Monthly dividend income", "money"), ("capital", "Capital needed for target", "money0")],
    js="""
var invested=v.shares*v.price, annual=v.shares*v.dividend, monthly=annual/12;
var yieldPct = invested>0 ? annual/invested*100 : 0;
var capital = yieldPct>0 ? v.target*12/(yieldPct/100) : 0;
return { invested: invested, annual: annual, monthly: monthly, capital: capital };
""",
    py=lambda v: {
        "invested": float(v["shares"]) * float(v["price"]),
        "annual": float(v["shares"]) * float(v["dividend"]),
        "monthly": float(v["shares"]) * float(v["dividend"]) / 12,
        "capital": ((float(v["target"]) * 12 / ((float(v["shares"]) * float(v["dividend"]) /
                     (float(v["shares"]) * float(v["price"]))) if float(v["shares"]) * float(v["price"]) > 0 else 0))
                    if float(v["shares"]) * float(v["dividend"]) > 0 else 0),
    },
    how="""<p>Dividend income is the annual dividend per share multiplied by the number of shares you own.
The <em>yield on cost</em> — annual income divided by what you paid — is the number that matters once
you own the shares; the current yield uses today's price and moves every day.</p>
<p>The capital-needed figure answers the retirement question: at this yield, how much would you have
to invest to produce a given monthly income? It ignores dividend growth, taxes and price changes.</p>""",
    formula="""<div class="fml"><code>annual income = shares × dividend per share
monthly income = annual income ÷ 12
yield on cost = annual income ÷ amount invested × 100
capital needed = target monthly income × 12 ÷ yield</code></div>
<p>500 shares at $40 paying $2.40 a year produce $1,200 a year ($100 a month) on $20,000 invested —
a 6% yield on cost. Producing $500 a month at that yield needs $100,000.</p>""",
    example="Your {invested} investment pays {annual} a year, or {monthly} a month. To reach your "
            "monthly target at this yield you would need {capital} invested.",
    mistakes=["<strong>Assuming the dividend is fixed.</strong> Companies cut dividends in recessions; "
              "a high yield can signal a payout about to fall.",
              "<strong>Ignoring tax.</strong> US qualified dividends are taxed at capital-gains rates, "
              "but REIT and foreign dividends are often taxed as ordinary income.",
              "<strong>Chasing yield.</strong> A 9% yield with a falling share price can lose more than "
              "the dividend pays."],
    faq=[("Is dividend income guaranteed?",
          "No. Dividends are declared by the company and can be reduced or stopped. Diversifying "
          "across many payers reduces the risk of one cut."),
         ("What is a good dividend yield?",
          "Broad-market funds typically yield 1-2%; individual high-yield stocks 4-6% but with more "
          "risk. Compare a stock's yield with its sector rather than in isolation."),
         ("Does the calculator account for dividend growth?",
          "No. It uses the dividend you enter as a constant. Growing dividends increase the effective "
          "yield over time, which the simple calculation ignores.")],
    related=["compound-interest", "401k-growth", "stock-profit-calculator"],
    note="Before tax. Dividends are not guaranteed and share prices change. Not investment advice.",
)


RENT_AFFORDABILITY = calc(
    slug="rent-affordability-calculator", name="Rent Affordability Calculator", cat="loans",
    title="Rent Affordability Calculator — How Much Rent Can You Afford?",
    desc="Find the rent your income supports using the 30% rule and a stricter 25% check, plus what "
         "is left for other spending.",
    h1="Rent affordability calculator",
    lede="Landlords and budget guides usually cap rent at 30% of gross income. Enter your income to see "
         "the rent that rule allows, a stricter 25% figure, and what remains each month.",
    fields=[num("income", "Gross monthly income", 5000, unit=MONEY, mn=0, mx=10**6),
            num("other", "Other monthly debt payments", 400, unit=MONEY, mn=0, mx=10**5),
            num("share", "Share of income for rent", 30, unit="%", mn=10, mx=60)],
    outs=[("rent", "Affordable rent", "money0"), ("strict", "At 25% of income", "money0"),
          ("annual", "Annual rent", "money0"), ("left", "Left for everything else", "money0")],
    js="""
var rent=v.income*v.share/100, strict=v.income*0.25;
var left=v.income-rent-v.other;
return { rent: rent, strict: strict, annual: rent*12, left: left };
""",
    py=lambda v: {
        "rent": float(v["income"]) * float(v["share"]) / 100,
        "strict": float(v["income"]) * 0.25,
        "annual": float(v["income"]) * float(v["share"]) / 100 * 12,
        "left": float(v["income"]) - float(v["income"]) * float(v["share"]) / 100 - float(v["other"]),
    },
    how="""<p>The 30% rule is a screening heuristic, not a law: it keeps rent low enough that utilities,
food, transport, savings and debt payments fit in the rest. In expensive cities many renters exceed
30%, which is why the 25% figure is shown — it is the level at which saving becomes comfortable.</p>
<p>Lenders use a related ratio, the debt-to-income ratio: total monthly debt including the proposed
rent should stay under about 36-43% of gross income for a mortgage application.</p>""",
    formula="""<div class="fml"><code>affordable rent = gross monthly income × rent share
at 25% = gross monthly income × 0.25
left over = income − rent − other debts</code></div>
<p>On $5,000 a month, the 30% rule allows $1,500 rent; at 25% it is $1,250. With $400 of other debt,
the 30% case leaves $3,100 for everything else.</p>""",
    example="At {share} of income your rent budget is {rent} a month ({annual} a year); a stricter 25% "
            "budget is {strict}. After rent and other debts you have {left} left each month.",
    mistakes=["<strong>Using net income.</strong> The rule uses gross income; applying it to take-home "
              "pay overstates what you can afford.",
              "<strong>Forgetting utilities and parking.</strong> Add 15-25% on top of rent for "
              "utilities, internet and any parking or pet fees.",
              "<strong>Ignoring a rent increase.</strong> Budget for the renewal, not just the "
              "first-year rent."],
    faq=[("Is the 30% rule realistic?",
          "In high-cost cities many households pay 35-50%. The rule is a starting point; what matters "
          "is whether the remainder covers essentials and savings."),
         ("Should I include utilities in the 30%?",
          "Ideally yes — the figure should cover housing costs, not just the rent cheque."),
         ("How do landlords check affordability?",
          "Commonly they want gross monthly income of 2.5-3 times the rent, plus a credit check.")],
    related=["mortgage-affordability", "savings-goal", "emergency-fund-calculator"],
    note="A budgeting heuristic based on gross income; your own fixed costs may differ.",
)


DOWN_PAYMENT = calc(
    slug="down-payment-calculator", name="Down Payment Calculator", cat="loans",
    title="Down Payment Calculator — Amount, Loan and Monthly Payment",
    desc="Work out the down payment on a home from the price and percentage, the loan amount, the "
         "monthly principal-and-interest payment and whether mortgage insurance applies.",
    h1="Down payment calculator",
    lede="Enter the home price, your down payment percentage, the rate and term to see the cash needed, "
         "the loan amount, the monthly payment and whether PMI is likely.",
    fields=[num("price", "Home price", 400000, unit=MONEY, mn=1000, mx=10**8),
            num("pct", "Down payment", 10, unit="%", mn=0, mx=100, step="0.5"),
            num("rate", "Mortgage rate", 6.5, unit="%", mn=0, mx=20, step="0.1"),
            num("years", "Loan term", 30, unit="years", mn=1, mx=40)],
    outs=[("down", "Down payment", "money0"), ("loan", "Loan amount", "money0"),
          ("monthly", "Monthly principal and interest", "money"), ("pmi", "Mortgage insurance likely", "text")],
    js="""
var down=v.price*v.pct/100, loan=v.price-down;
var r=v.rate/100/12, n=Math.round(v.years*12);
var pmt = loan<=0 ? 0 : (r>0 ? loan*r/(1-Math.pow(1+r,-n)) : loan/n);
return { down: down, loan: loan, monthly: pmt, pmi: v.pct<20 ? "Yes — under 20% down" : "No — 20% or more" };
""",
    py=lambda v: {
        "down": float(v["price"]) * float(v["pct"]) / 100,
        "loan": float(v["price"]) - float(v["price"]) * float(v["pct"]) / 100,
        "monthly": (lambda loan, r, n: 0.0 if loan <= 0 else (loan * r / (1 - (1 + r) ** -n) if r > 0 else loan / n))(
            float(v["price"]) - float(v["price"]) * float(v["pct"]) / 100,
            float(v["rate"]) / 100 / 12, int(float(v["years"]) * 12)),
        "pmi": "Yes — under 20% down" if float(v["pct"]) < 20 else "No — 20% or more",
    },
    how="""<p>The down payment is the part of the price you pay in cash; the rest is the mortgage. A larger
down payment lowers both the loan and the monthly payment, and usually the interest rate.</p>
<p>In the US, a down payment below 20% typically means private mortgage insurance (PMI) until the loan
balance falls to about 80% of the home value. PMI protects the lender, not you, and adds roughly
0.3-1.5% of the loan amount per year.</p>""",
    formula="""<div class="fml"><code>down payment = price × down-payment percentage
loan amount = price − down payment
monthly payment = loan × r ÷ (1 − (1 + r)^−n)
  where r = annual rate ÷ 12 and n = years × 12</code></div>
<p>A $400,000 home with 10% down: $40,000 cash, a $360,000 loan, and at 6.5% over 30 years a monthly
principal-and-interest payment of $2,275.</p>""",
    example="A {pct} down payment on a {price} home is {down} in cash, leaving a {loan} loan. At the "
            "rate and term entered the monthly principal and interest is {monthly}. Mortgage insurance: {pmi}.",
    mistakes=["<strong>Spending all your cash on the down payment.</strong> Keep an emergency fund and "
              "closing costs (2-5% of the price) in reserve.",
              "<strong>Forgetting PMI.</strong> Under 20% down the monthly cost is higher than the "
              "payment alone.",
              "<strong>Ignoring property tax and insurance.</strong> Escrow payments often add "
              "hundreds a month on top of principal and interest."],
    faq=[("How much down payment do I need?",
          "Conventional loans often allow 3-5%; FHA loans 3.5%; 20% avoids mortgage insurance and "
          "usually gets the best rate."),
         ("Can the down payment come from a gift?",
          "Often yes, with a gift letter. Lenders require documentation of the source of funds."),
         ("Does a bigger down payment always make sense?",
          "Not always: at low rates, keeping cash invested can beat the interest saved. It depends on "
          "your rate, risk tolerance and reserves.")],
    related=["mortgage-payment", "mortgage-affordability", "refinance-breakeven"],
    note="Principal and interest only; excludes property tax, insurance, HOA and PMI amounts.",
)


SE_TAX = calc(
    slug="self-employment-tax-calculator", name="Self-Employment Tax Calculator", cat="salary",
    title="Self-Employment Tax Calculator — US 1099 Social Security and Medicare",
    desc="Calculate US self-employment tax on 1099 income: the Social Security and Medicare "
         "contributions, the deductible half, and the effective rate.",
    h1="Self-employment tax calculator",
    lede="Self-employed Americans pay both halves of Social Security and Medicare. Enter your net "
         "self-employment profit to see the tax, the deduction and what is left.",
    fields=[num("profit", "Net self-employment profit", 80000, unit=MONEY, mn=0, mx=10**7),
            num("sswage", "W-2 wages already subject to Social Security", 0, unit=MONEY, mn=0, mx=10**7),
            num("expenses", "Deductible business expenses", 0, unit=MONEY, mn=0, mx=10**7)],
    outs=[("taxable", "Profit after expenses", "money0"), ("se", "Self-employment tax", "money0"),
          ("half", "Deductible half", "money0"), ("rate", "Effective SE rate", "pct1")],
    js="""
var profit=Math.max(0, v.profit - v.expenses);
var base=profit*0.9235;
var ssCap=168600;                       // 2024 Social Security wage base
var ssRoom=Math.max(0, ssCap - v.sswage);
var ss=Math.min(base, ssRoom)*0.124;
var medicare=base*0.029;
var se=ss+medicare;
return { taxable: profit, se: se, half: se/2, rate: profit>0 ? se/profit*100 : 0 };
""",
    py=lambda v: {
        "taxable": max(0.0, float(v["profit"]) - float(v["expenses"])),
        "se": (lambda profit, ssw: (min(max(0.0, profit) * 0.9235, max(0.0, 168600 - ssw)) * 0.124
                                    + max(0.0, profit) * 0.9235 * 0.029))(
            max(0.0, float(v["profit"]) - float(v["expenses"])), float(v["sswage"])),
        "half": (lambda profit, ssw: (min(max(0.0, profit) * 0.9235, max(0.0, 168600 - ssw)) * 0.124
                                      + max(0.0, profit) * 0.9235 * 0.029) / 2)(
            max(0.0, float(v["profit"]) - float(v["expenses"])), float(v["sswage"])),
        "rate": (lambda profit, ssw: (((min(max(0.0, profit) * 0.9235, max(0.0, 168600 - ssw)) * 0.124
                                        + max(0.0, profit) * 0.9235 * 0.029) / profit * 100)
                                      if profit > 0 else 0))(
            max(0.0, float(v["profit"]) - float(v["expenses"])), float(v["sswage"])),
    },
    how="""<p>Employees split Social Security and Medicare tax with their employer: 6.2% + 1.45% each.
The self-employed pay both halves — 12.4% for Social Security and 2.9% for Medicare — on 92.35% of
net profit. That is why the effective rate is about 14.13%, not 15.3%.</p>
<p>Social Security tax applies only up to the annual wage base ($168,600 in 2024), reduced by any W-2
wages you already have. Medicare has no cap, and higher earners pay an additional 0.9%. Half of the
self-employment tax is deductible against income tax.</p>""",
    formula="""<div class="fml"><code>taxable base = net profit × 92.35%
Social Security = 12.4% × min(base, wage-base − W-2 wages)
Medicare = 2.9% × base
self-employment tax = Social Security + Medicare
deductible half = self-employment tax ÷ 2</code></div>
<p>On $80,000 of profit the tax is about $11,304 (14.1%), half of which — $5,652 — is deductible
against income tax.</p>""",
    example="On {taxable} of profit the self-employment tax is {se} — an effective rate of {rate}. "
            "Half of it, {half}, is deductible against income tax.",
    mistakes=["<strong>Forgetting quarterly payments.</strong> Self-employed people generally pay "
              "estimated tax four times a year; missing them triggers penalties.",
              "<strong>Not deducting the half.</strong> The employer-half deduction reduces taxable "
              "income and is easy to overlook.",
              "<strong>Mixing profit and revenue.</strong> The tax applies to net profit after "
              "expenses, not gross receipts."],
    faq=[("Do I pay self-employment tax on top of income tax?",
          "Yes — self-employment tax funds Social Security and Medicare; federal and state income tax "
          "are separate and calculated on profit after the deductible half."),
         ("What is the 92.35% figure?",
          "It approximates the employee's share of FICA that the self-employed do not pay twice, so the "
          "tax base is reduced accordingly."),
         ("What is the 2024 Social Security wage base?",
          "$168,600. Above that, only the 2.9% Medicare portion applies.")],
    related=["paycheck-net-estimate", "hourly-to-salary", "tax-bracket"],
    note="Estimate for US federal self-employment tax only (2024 rules); excludes income tax and state tax.",
)


CALCS = [DIVIDEND_INCOME, RENT_AFFORDABILITY, DOWN_PAYMENT, SE_TAX]
