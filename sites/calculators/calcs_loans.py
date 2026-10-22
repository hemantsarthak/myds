#!/usr/bin/env python3
"""Loans calculators: payment, mortgage, amortisation, auto, student, cards,
affordability, rent-vs-buy, refinance break-even."""
from core import calc, num, sel, fnum, fmt_date, table_html

# ---------------------------------------------------------------------------
# 1. generic loan payment
MONEY = "USD"


def _loan_py(v):
    P = float(v["amount"])
    r = float(v["rate"]) / 100 / 12
    n = max(1, int(round(float(v["years"]) * 12)))
    m = P * r * (1 + r) ** n / ((1 + r) ** n - 1) if r > 0 else P / n
    total = m * n
    return {"payment": m, "total": total, "interest": total - P, "principal": P}


LOAN_PAYMENT = calc(
    slug="loan-payment", name="Loan Payment Calculator", cat="loans",
    title="Loan Payment Calculator — Monthly Payment & Total Interest",
    desc="Work out the monthly payment, total repayment and total interest on any fixed-rate loan. "
         "Enter amount, APR and term to see the real cost of borrowing.",
    h1="Loan payment calculator",
    lede="Enter a loan amount, annual interest rate and term to get the fixed monthly payment and "
         "the total interest you will pay over the life of the loan.",
    fields=[num("amount", "Loan amount", 20000, unit=MONEY, pre="$", mn=100, mx=100000000, step=100),
            num("rate", "Annual interest rate", 8, unit="APR %", mn=0, mx=60, step="0.01"),
            num("years", "Loan term", 5, unit="years", mn=1, mx=40, step=1)],
    outs=[("payment", "Monthly payment", "money"), ("total", "Total repaid", "money"),
          ("interest", "Total interest", "money")],
    viz=[("Principal", "principal", "money"), ("Interest", "interest", "money")],
    js="""
var P = v.amount, r = v.rate / 100 / 12, n = Math.max(1, Math.round(v.years * 12));
var m = r > 0 ? P * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1) : P / n;
return { payment: m, total: m * n, interest: m * n - P, principal: P };
""",
    py=_loan_py,
    how="""<p>A fixed-rate loan splits every payment into two parts: interest on the balance that is
still outstanding, and principal that reduces the balance. Because interest is charged on a
shrinking balance, the interest portion is largest in the first payment and falls slowly, while
the principal portion grows. The monthly amount stays identical for the whole term — that is the
point of a fixed-rate loan — but the mix inside each payment changes every month.</p>
<p>This calculator solves the standard amortisation formula directly, so it works for personal
loans, car finance, a mortgage or any other fully amortising loan where the rate never changes.
It assumes payments are made monthly and at the end of each month.</p>""",
    formula="""<p>For loan principal <em>P</em>, monthly interest rate <em>r</em> (annual APR ÷ 12 ÷ 100)
and <em>n</em> monthly payments, the fixed payment <em>M</em> is:</p>
<div class="fml"><code>M = P · r · (1 + r)^n / ((1 + r)^n − 1)</code></div>
<p>Total repaid is simply <em>M × n</em>, and total interest is that total minus the amount
borrowed. When the rate is 0% the formula reduces to <em>P / n</em>.</p>""",
    example="With the default numbers a {amount} loan at {rate}% over {years} years costs "
            "{payment} a month. Across the term that is {total} repaid, of which {interest} is "
            "interest — the difference between the price of the loan and its balance.",
    mistakes=[
        "<strong>Using the APR as a monthly rate.</strong> A 8% APR is about 0.667% per month. "
        "Feeding 8 straight into the formula overstates the payment by roughly twelve times.",
        "<strong>Ignoring fees.</strong> Origination fees and insurance are not in the payment "
        "formula. Add them to the amount borrowed to see their true cost.",
        "<strong>Comparing payments only.</strong> A longer term lowers the payment but raises total "
        "interest. Compare the total repaid column, not just the monthly figure.",
    ],
    faq=[
        ("What is a good interest rate for a personal loan?",
         "It depends on your credit profile, loan amount and term. In the US, well-qualified "
         "borrowers typically see single-digit APRs on unsecured personal loans, while rates above "
         "the mid-teens usually signal a higher-risk profile or a very small loan. Compare at least "
         "three offers and look at the APR, which includes fees, not just the headline rate."),
        ("Does paying early reduce the interest?",
         "Yes. Interest is charged on the outstanding balance, so any extra principal payment "
         "removes interest from every later payment. On this calculator, total interest assumes the "
         "minimum payment for the full term; extra payments shorten the loan and cut the total."),
        ("What is the difference between APR and interest rate?",
         "The interest rate is the cost of the borrowed money. The APR also folds in most upfront "
         "fees, so it is usually slightly higher and is the better number for comparing offers."),
    ],
    related=["mortgage-payment", "auto-loan", "student-loan", "credit-card-payoff"],
    note="Assumes a fixed rate and monthly payments; fees and insurance are not included.",
)


# ---------------------------------------------------------------------------
# 2. mortgage payment
def _mortgage_py(v):
    P = float(v["amount"])
    r = float(v["rate"]) / 100 / 12
    n = max(1, int(round(float(v["years"]) * 12)))
    m = P * r * (1 + r) ** n / ((1 + r) ** n - 1) if r > 0 else P / n
    return {"payment": m, "total": m * n, "interest": m * n - P, "principal": P}


MORTGAGE_PAYMENT = calc(
    slug="mortgage-payment", name="Mortgage Payment Calculator", cat="loans",
    title="Mortgage Payment Calculator — Principal & Interest",
    desc="Calculate the principal-and-interest payment on a fixed-rate mortgage, plus total "
         "interest and total cost. See how the rate and term change the monthly payment.",
    h1="Mortgage payment calculator",
    lede="Work out the principal-and-interest payment on a fixed-rate mortgage, and see how much "
         "of the total goes to interest over the term.",
    fields=[num("amount", "Mortgage amount", 250000, unit=MONEY, pre="$", mn=1000, mx=20000000, step=1000),
            num("rate", "Interest rate", 6, unit="APR %", mn=0, mx=25, step="0.01"),
            num("years", "Term", 30, unit="years", mn=1, mx=40, step=1)],
    outs=[("payment", "Monthly payment (P&I)", "money"), ("total", "Total repaid", "money"),
          ("interest", "Total interest", "money")],
    viz=[("Principal", "principal", "money"), ("Interest", "interest", "money")],
    js="""
var P = v.amount, r = v.rate / 100 / 12, n = Math.max(1, Math.round(v.years * 12));
var m = r > 0 ? P * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1) : P / n;
return { payment: m, total: m * n, interest: m * n - P, principal: P };
""",
    py=_mortgage_py,
    how="""<p>This is the principal-and-interest (P&amp;I) part of a mortgage payment — the amount that
repays the loan itself. Your real monthly bill usually also includes property tax, homeowners
insurance and possibly mortgage insurance, which lenders collect in escrow and which are not part
of this calculation.</p>
<p>The maths is identical to any amortising loan, but the numbers matter more because the term is
long. At 6% over 30 years, more than half of every early payment is interest. A shorter term or a
lower rate shifts that balance dramatically: a 15-year loan at the same rate carries a payment
about 35% higher but cuts total interest by roughly 60%.</p>""",
    formula="""<p>For mortgage amount <em>P</em>, monthly rate <em>r</em> = APR ÷ 12 ÷ 100 and
<em>n</em> = term in months:</p>
<div class="fml"><code>M = P · r · (1 + r)^n / ((1 + r)^n − 1)</code></div>
<p>Multiply <em>M</em> by <em>n</em> for total payments; subtract <em>P</em> for total interest.
The common shortcut “multiply the loan by 6% for a 30-year loan” is not accurate — the true total
interest at 6% over 30 years is about 116% of the amount borrowed.</p>""",
    example="The default {amount} mortgage at {rate}% for {years} years has a principal-and-interest "
            "payment of {payment}. Over the full term you would repay {total}, so {interest} — "
            "more than the amount originally borrowed — goes to interest.",
    mistakes=[
        "<strong>Forgetting escrow.</strong> Property tax and insurance can add 20–40% to the P&amp;I "
        "figure. Budget with a full PITI estimate, not just this number.",
        "<strong>Comparing rates without points.</strong> A lower rate bought with discount points is "
        "not free; divide the point cost by the monthly saving to see the break-even months.",
        "<strong>Assuming the payment never changes.</strong> This figure is for a fixed-rate loan. "
        "Adjustable-rate mortgages reset on a schedule and can move sharply.",
    ],
    faq=[
        ("Is it better to choose a 15-year or 30-year mortgage?",
         "A 15-year loan usually has a lower rate and much less total interest, but the payment is "
         "substantially higher. Choose the shorter term only if the payment fits comfortably within "
         "your budget; a 30-year loan with extra principal payments keeps flexibility while still "
         "saving interest."),
        ("How much house can I afford on this payment?",
         "Lenders typically cap the total housing payment at around 28% of gross monthly income and "
         "all debt payments at 36–43%. Divide the payment you can afford by that ratio to estimate "
         "the income required; the mortgage affordability calculator does the full calculation."),
        ("What is included in a mortgage payment?",
         "A standard US mortgage bill contains four parts: principal, interest, property tax and "
         "homeowners insurance (PITI). If the down payment is below 20%, private mortgage insurance "
         "may be added too."),
    ],
    related=["mortgage-amortization", "mortgage-affordability", "refinance-breakeven", "rent-vs-buy"],
    note="Principal and interest only. Property tax, insurance and mortgage insurance are extra.",
)


# ---------------------------------------------------------------------------
# 3. mortgage amortisation schedule
def _amort_rows(v):
    P = float(v["amount"])
    r = float(v["rate"]) / 100 / 12
    n = max(1, int(round(float(v["years"]) * 12)))
    m = P * r * (1 + r) ** n / ((1 + r) ** n - 1) if r > 0 else P / n
    bal, yint, yprin, rows, yi = P, 0.0, 0.0, [], 0
    for i in range(1, n + 1):
        interest = bal * r
        principal = m - interest
        if i == n:
            principal = bal
        bal = max(0.0, bal - principal)
        yint += interest
        yprin += principal
        if i % 12 == 0 or i == n:
            yi += 1
            rows.append([str(yi), "$" + fnum(yint, 0), "$" + fnum(yprin, 0), "$" + fnum(bal, 0)])
            yint = yprin = 0.0
    return m, rows


def _amort_py(v):
    m, _rows = _amort_rows(v)
    r = float(v["rate"]) / 100 / 12
    P = float(v["amount"])
    n = max(1, int(round(float(v["years"]) * 12)))
    first_i = P * r
    return {"payment": m, "total": m * n, "interest": m * n - P, "first_interest": first_i,
            "first_principal": m - first_i}


def _amort_table(v):
    _m, rows = _amort_rows(v)
    return table_html(["Year", "Interest paid", "Principal paid", "Balance left"], rows)


EXTRA_AMORT = r"""
function d(x){var n=Math.floor(x*100+0.5)/100,neg=n<0;if(neg)n=-n;var s=n.toFixed(2),p=s.split('.');
  return (neg?'-':'')+'$'+p[0].replace(/\B(?=(\d{3})+(?!\d))/g,',')+'.'+p[1];}
var P=v.amount,r=v.rate/100/12,n=Math.max(1,Math.round(v.years*12));
var m=r>0?P*r*Math.pow(1+r,n)/(Math.pow(1+r,n)-1):P/n;
var bal=P,yi=0,yint=0,yprin=0,rows='';
for(var i=1;i<=n;i++){
  var it=bal*r, pr=m-it; if(i===n) pr=bal;
  bal=Math.max(0,bal-pr); yint+=it; yprin+=pr;
  if(i%12===0||i===n){
    yi++; rows+='<tr><td>'+yi+'</td><td>'+d(yint)+'</td><td>'+d(yprin)+'</td><td>'+d(bal)+'</td></tr>';
    yint=0;yprin=0;
  }
}
var t=document.getElementById('tbl');
if(t) t.innerHTML='<div class="tw"><table><thead><tr><th>Year</th><th>Interest paid</th><th>Principal paid</th><th>Balance left</th></tr></thead><tbody>'+rows+'</tbody></table></div>';
"""

AMORTIZATION = calc(
    slug="mortgage-amortization", name="Mortgage Amortisation Calculator", cat="loans",
    title="Mortgage Amortisation Schedule — Year-by-Year Breakdown",
    desc="See exactly how a fixed-rate mortgage is paid down: monthly payment, first-month "
         "principal and interest, and a year-by-year amortisation schedule down to a zero balance.",
    h1="Mortgage amortisation calculator",
    lede="See how each payment splits between interest and principal, and follow the balance down "
         "year by year until the mortgage is repaid.",
    fields=[num("amount", "Mortgage amount", 250000, unit=MONEY, pre="$", mn=1000, mx=20000000, step=1000),
            num("rate", "Interest rate", 6, unit="APR %", mn=0, mx=25, step="0.01"),
            num("years", "Term", 30, unit="years", mn=1, mx=40, step=1)],
    outs=[("payment", "Monthly payment", "money"),
          ("first_interest", "First payment: interest", "money"),
          ("first_principal", "First payment: principal", "money"),
          ("interest", "Total interest", "money")],
    js="""
var P=v.amount,r=v.rate/100/12,n=Math.max(1,Math.round(v.years*12));
var m=r>0?P*r*Math.pow(1+r,n)/(Math.pow(1+r,n)-1):P/n;
var fi=P*r;
return {payment:m,total:m*n,interest:m*n-P,first_interest:fi,first_principal:m-fi};
""",
    py=_amort_py,
    table={"title": "Amortisation schedule (year by year)"},
    py_table=_amort_table,
    extra_js=EXTRA_AMORT,
    how="""<p>An amortisation schedule is the month-by-month ledger of a mortgage. Each payment first
covers the interest accrued on the remaining balance, and whatever is left reduces the principal.
Your payment is fixed, but the split is not: on a 30-year loan at 6%, the first payment is
$1,250 of interest and only about $249 of principal, while the final payment is almost entirely
principal.</p>
<p>The table below is generated from the same formula as the calculator and shows, for each year,
how much interest you paid, how much principal you cleared and what is still owed. It is the
schedule lenders use, assuming no extra payments, no late fees and a fixed rate. Any extra
principal you pay shortens the schedule and moves every later row forward.</p>""",
    formula="""<p>Payment <em>M</em> comes from the standard amortisation formula with
<em>r</em> = APR ÷ 12 ÷ 100 and <em>n</em> = months. For month <em>i</em>:</p>
<div class="fml"><code>interest_i = balance_(i−1) × r
principal_i = M − interest_i
balance_i = balance_(i−1) − principal_i</code></div>
<p>The final payment is adjusted down so the balance lands exactly on zero. Total interest is
<em>M × n − P</em>.</p>""",
    example="On a {amount} mortgage at {rate}% over {years} years the payment is {payment}. The first "
            "payment contains {first_interest} of interest and only {first_principal} of principal. "
            "Across the whole term you pay {interest} in interest. The table below shows the same "
            "numbers totalled by year.",
    mistakes=[
        "<strong>Reading the first month as typical.</strong> The early schedule is mostly interest. "
        "Halfway through a 30-year loan the balance is still around 75% of the original amount.",
        "<strong>Ignoring the effect of extra payments.</strong> An extra $100 a month this early is "
        "not just $100 off the total — it removes all future interest on that amount, which is why "
        "small prepayments shorten a 30-year loan by years.",
        "<strong>Assuming the schedule covers taxes.</strong> Escrowed property tax and insurance do "
        "not amortise at all. Only the principal-and-interest part follows this schedule.",
    ],
    faq=[
        ("What does amortisation mean?",
         "Amortisation is the process of paying a loan down through regular payments that cover "
         "both interest and principal. A fully amortising loan ends with a zero balance exactly at "
         "the end of its term."),
        ("Why is most of my early payment interest?",
         "Interest is charged on the entire outstanding balance. At the start the balance is at its "
         "largest, so the interest charge is largest; as the balance falls, more of each payment can "
         "go to principal."),
        ("How much faster does the loan pay off with extra payments?",
         "It depends on when the extra payments start and how large they are. Paying even a small "
         "extra amount in the first years has a disproportionate effect because it removes interest "
         "from every following month. Recalculate with a lower loan amount to approximate the effect "
         "of a lump-sum prepayment."),
    ],
    related=["mortgage-payment", "refinance-breakeven", "loan-payment", "mortgage-affordability"],
    note="Fixed rate, no extra payments, no fees. Amounts rounded to the nearest dollar.",
)


# ---------------------------------------------------------------------------
# 4. auto loan
def _auto_py(v):
    financed = max(0.0, float(v["price"]) - float(v["down"]))
    r = float(v["rate"]) / 100 / 12
    n = max(1, int(round(float(v["years"]) * 12)))
    m = financed * r * (1 + r) ** n / ((1 + r) ** n - 1) if r > 0 else financed / n
    total = m * n
    return {"payment": m, "financed": financed, "interest": total - financed,
            "total": total + float(v["down"]), "principal": financed}


AUTO_LOAN = calc(
    slug="auto-loan", name="Auto Loan Calculator", cat="loans",
    title="Auto Loan Calculator — Monthly Car Payment & Total Cost",
    desc="Calculate a car loan payment from the vehicle price, down payment, trade-in value, APR "
         "and term. See the amount financed, total interest and total cost of the car.",
    h1="Auto loan calculator",
    lede="Enter the vehicle price, what you pay upfront and the loan terms to see the monthly "
         "payment and what the car really costs once interest is included.",
    fields=[num("price", "Vehicle price", 32000, unit=MONEY, pre="$", mn=500, mx=1000000, step=500),
            num("down", "Down payment / trade-in", 4000, unit=MONEY, pre="$", mn=0, mx=1000000, step=500),
            num("rate", "Loan APR", 6.9, unit="%", mn=0, mx=35, step="0.01"),
            num("years", "Loan term", 5, unit="years", mn=1, mx=10, step=1)],
    outs=[("payment", "Monthly payment", "money"), ("financed", "Amount financed", "money"),
          ("interest", "Total interest", "money"), ("total", "Total outlay (incl. down payment)", "money")],
    viz=[("Financed", "principal", "money"), ("Interest", "interest", "money")],
    js="""
var P = Math.max(0, v.price - v.down), r = v.rate / 100 / 12, n = Math.max(1, Math.round(v.years * 12));
var m = r > 0 ? P * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1) : P / n;
var total = m * n;
return { payment: m, financed: P, interest: total - P, total: total + v.down, principal: P };
""",
    py=_auto_py,
    how="""<p>Car finance works like any other fixed-rate loan, but two details matter more than on a
mortgage. First, the down payment and any trade-in reduce the amount financed directly, so every
dollar upfront also removes interest from the whole term. Second, cars depreciate quickly: a
five-year loan on a new car often ends with the balance close to or above the car's market value,
which is what people mean by being “underwater”.</p>
<p>This calculator returns the amount financed, the monthly payment, the interest over the term,
and the total outlay including what you paid upfront. Dealer fees, sales tax, registration and
optional extras are not included; add them to the vehicle price if you want them in the payment.</p>""",
    formula="""<p>Amount financed <em>F = price − down payment</em>. With monthly rate
<em>r</em> = APR ÷ 12 ÷ 100 and <em>n</em> months:</p>
<div class="fml"><code>M = F · r · (1 + r)^n / ((1 + r)^n − 1)
total outlay = M · n + down payment</code></div>
<p>Total interest is <em>M × n − F</em>. A zero-percent loan reduces the payment to
<em>F / n</em>.</p>""",
    example="A {price} car with a {down} down payment leaves {financed} to finance. At {rate}% over "
            "{years} years the payment is {payment} a month, total interest is {interest}, and the "
            "full outlay including the down payment is {total}.",
    mistakes=[
        "<strong>Stretching the term to hit a payment.</strong> A 84-month loan can leave you owing "
        "more than the car is worth for years. Compare total interest, not just the monthly number.",
        "<strong>Leaving out tax and fees.</strong> Sales tax, registration and dealer documentation "
        "fees are often financed, which raises both the payment and the interest.",
        "<strong>Skipping the down payment.</strong> Zero-down car loans are the quickest route to "
        "negative equity. A 10–20% down payment keeps the loan closer to the car's value.",
    ],
    faq=[
        ("How much car can I afford?",
         "A common guideline is to keep total transport costs — payment, insurance, fuel and "
         "maintenance — below 15–20% of take-home pay. Lenders also look at debt-to-income: the car "
         "payment plus other debts should generally stay under about 36% of gross income."),
        ("Is a longer car loan cheaper?",
         "The monthly payment is lower, but total interest is higher and the car has more time to "
         "depreciate below the loan balance. The only reason to take a longer term is cash-flow "
         "pressure that you expect to be temporary."),
        ("Does a trade-in reduce interest?",
         "Yes. The trade-in value reduces the amount financed, which lowers every monthly payment "
         "and therefore the total interest. In most US states, a trade-in also reduces the sales tax "
         "base."),
    ],
    related=["loan-payment", "credit-card-payoff", "mortgage-payment", "student-loan"],
    note="Finance charges only. Sales tax, registration, insurance and dealer fees are not included.",
)


# ---------------------------------------------------------------------------
# 5. student loan
def _student_py(v):
    P = float(v["amount"])
    r = float(v["rate"]) / 100 / 12
    n = max(1, int(round(float(v["years"]) * 12)))
    m = P * r * (1 + r) ** n / ((1 + r) ** n - 1) if r > 0 else P / n
    return {"payment": m, "total": m * n, "interest": m * n - P, "principal": P}


STUDENT_LOAN = calc(
    slug="student-loan", name="Student Loan Calculator", cat="loans",
    title="Student Loan Calculator — Monthly Payment & Repayment Cost",
    desc="Calculate the standard repayment payment on a student loan and see total interest. "
         "Compare the cost of different rates and repayment terms.",
    h1="Student loan payment calculator",
    lede="Estimate the fixed monthly payment on a student loan under standard repayment, and see "
         "how much of your total payments go to interest.",
    fields=[num("amount", "Loan balance", 40000, unit=MONEY, pre="$", mn=500, mx=1000000, step=500),
            num("rate", "Interest rate", 5.5, unit="APR %", mn=0, mx=20, step="0.01"),
            num("years", "Repayment term", 10, unit="years", mn=1, mx=30, step=1)],
    outs=[("payment", "Monthly payment", "money"), ("total", "Total repaid", "money"),
          ("interest", "Total interest", "money")],
    viz=[("Principal", "principal", "money"), ("Interest", "interest", "money")],
    js="""
var P = v.amount, r = v.rate / 100 / 12, n = Math.max(1, Math.round(v.years * 12));
var m = r > 0 ? P * r * Math.pow(1 + r, n) / (Math.pow(1 + r, n) - 1) : P / n;
return { payment: m, total: m * n, interest: m * n - P, principal: P };
""",
    py=_student_py,
    how="""<p>The US standard repayment plan for federal student loans spreads the balance evenly over
ten years with a fixed payment. Private student loans often use the same amortisation but may have
shorter or longer terms, variable rates and different deferment rules. This calculator models the
classic fixed-rate, fully amortising case so you can see what standard repayment actually costs.</p>
<p>Two things are not modelled because they depend on your specific situation: income-driven
repayment (which caps payments at a percentage of discretionary income for 20–25 years) and
forgiveness programmes. Both can change the total dramatically, but they also depend on
eligibility and tax rules that no simple formula can capture.</p>""",
    formula="""<p>Standard amortisation with <em>P</em> = balance, <em>r</em> = APR ÷ 12 ÷ 100 and
<em>n</em> = months in the term:</p>
<div class="fml"><code>M = P · r · (1 + r)^n / ((1 + r)^n − 1)</code></div>
<p>Interest is charged on the outstanding balance each month. During any deferment or forbearance
period interest may still accrue, so the starting balance in repayment can be higher than what you
originally borrowed — use the post-graduation balance here.</p>""",
    example="A {amount} student loan at {rate}% over {years} years requires {payment} a month. The "
            "total repaid is {total}, which means {interest} of interest on top of the balance.",
    mistakes=[
        "<strong>Using the pre-graduation balance.</strong> If interest was capitalised during "
        "school or a grace period, the repayment balance is larger. Start from the actual figure "
        "your servicer reports.",
        "<strong>Assuming income-driven plans are cheaper overall.</strong> Lower monthly payments "
        "usually mean a longer term and more interest, and forgiveness may be taxable depending on "
        "the programme and your jurisdiction.",
        "<strong>Ignoring the interest deduction.</strong> In the US, some student loan interest is "
        "tax-deductible (subject to income limits), which slightly reduces the true cost. This "
        "calculator shows the gross cost.",
    ],
    faq=[
        ("What is the standard student loan repayment term?",
         "For most US federal student loans, standard repayment is a fixed 10-year schedule. "
         "Consolidation can stretch this up to 30 years, and private lenders commonly offer 5–15 "
         "year terms."),
        ("Should I pay extra on a student loan?",
         "Compare the interest rate with your alternatives. Federal loans above roughly 6–7% are "
         "usually worth prioritising over investing in low-risk accounts; lower-rate federal loans "
         "may be worth keeping while you build an emergency fund or contribute to a retirement "
         "match."),
        ("Does refinancing a student loan make sense?",
         "Refinancing can lower the rate if your credit has improved, but it replaces federal loans "
         "with a private loan, giving up income-driven repayment and forgiveness eligibility. Check "
         "the break-even on the closing costs and the new term before deciding."),
    ],
    related=["loan-payment", "credit-card-payoff", "paycheck-net", "mortgage-payment"],
    note="Standard fixed-rate repayment only. Income-driven plans, deferment and forgiveness are not modelled.",
)


# ---------------------------------------------------------------------------
# 6. credit card payoff
def _cc_py(v):
    bal = float(v["balance"])
    payment = float(v["payment"])
    r = float(v["apr"]) / 100 / 12
    if payment <= bal * r:
        return {"months": "Never", "interest": float("inf"), "total": float("inf")}
    m = 0
    interest = 0.0
    while bal > 0 and m < 2400:
        i = bal * r
        interest += i
        bal = bal + i - payment
        m += 1
    if bal > 0:
        return {"months": "Over 100 years", "interest": float("inf"), "total": float("inf")}
    return {"months": f"{m} months", "interest": interest, "total": float(v["balance"]) + interest}


CREDIT_CARD = calc(
    slug="credit-card-payoff", name="Credit Card Payoff Calculator", cat="loans",
    title="Credit Card Payoff Calculator — How Long to Clear Your Balance",
    desc="See how long a credit card balance takes to clear at a fixed monthly payment, and how "
         "much interest you pay. Find the payment needed to be debt-free.",
    h1="Credit card payoff calculator",
    lede="Enter a balance, the card's APR and the amount you can pay each month to see when the "
         "balance reaches zero and how much interest it costs along the way.",
    fields=[num("balance", "Card balance", 5000, unit=MONEY, pre="$", mn=50, mx=1000000, step=50),
            num("apr", "Purchase APR", 22, unit="%", mn=0, mx=99, step="0.01"),
            num("payment", "Monthly payment", 200, unit=MONEY, pre="$", mn=10, mx=1000000, step=10)],
    outs=[("months", "Time to pay off", "text"), ("interest", "Total interest", "money"),
          ("total", "Total paid", "money")],
    js="""
var bal = v.balance, r = v.apr / 100 / 12, pay = v.payment;
if (pay <= bal * r) return { months: 'Never', interest: Infinity, total: Infinity };
var m = 0, interest = 0;
while (bal > 0 && m < 2400) { var i = bal * r; interest += i; bal = bal + i - pay; m += 1; }
if (bal > 0) return { months: 'Over 100 years', interest: Infinity, total: Infinity };
return { months: m + ' months', interest: interest, total: v.balance + interest };
""",
    py=_cc_py,
    how="""<p>Credit card interest is calculated on the average daily balance, but a monthly model is
accurate enough to show how a fixed payment behaves. The trap is the minimum payment: card issuers
usually calculate it as about 1–3% of the balance, so as the balance falls the minimum falls with
it. Paying only the minimum can stretch a few thousand dollars over a decade or more.</p>
<p>This calculator assumes you pay the same amount every month and stop using the card. If the
payment is less than the interest charged in the first month, the balance grows and the card will
never be repaid — the tool says so explicitly.</p>""",
    formula="""<p>Each month the interest charge is <em>balance × APR ÷ 12 ÷ 100</em>, the balance becomes
<em>balance + interest − payment</em>, and the process repeats until the balance reaches zero.
There is no single closed-form payment for a chosen number of months, so the calculator loops the
monthly step directly — the same way your statement does.</p>""",
    example="A {balance} balance at {apr}% APR with a {payment} monthly payment clears in {months}. "
            "By the time it is paid off you will have paid {interest} in interest and {total} in "
            "total, assuming you never add new charges.",
    mistakes=[
        "<strong>Paying only the minimum.</strong> Minimum payments fall as the balance falls, which "
        "keeps the loan alive for years. Fix a payment amount instead.",
        "<strong>Using the card again.</strong> Every new charge is usually at the highest rate on "
        "the card. A payoff plan only works if the balance stops growing.",
        "<strong>Ignoring a 0% promotional rate expiry.</strong> The standard purchase APR returns "
        "when the promo ends, and often on the whole remaining balance. Calculate with the rate that "
        "will apply, not the teaser rate.",
    ],
    faq=[
        ("How long does it take to pay off a credit card?",
         "It depends on the balance, rate and payment. A $5,000 balance at 22% with a $200 monthly "
         "payment takes roughly three years; dropping the payment to $100 roughly doubles both the "
         "time and the interest."),
        ("What payment do I need to be debt-free in a year?",
         "Work backwards: decide the number of months, and use the loan payment formula with the "
         "card APR and term to get the required fixed payment. Always round up — statement interest "
         "and new charges add a little."),
        ("Is it better to pay the highest-rate card first?",
         "Mathematically yes: paying the highest APR first (the avalanche method) costs the least "
         "interest. The snowball method — smallest balance first — is often more motivating and "
         "therefore may work better in practice."),
    ],
    related=["loan-payment", "student-loan", "auto-loan", "savings-goal"],
    note="Assumes no new charges and a fixed monthly payment. Issuer minimum-payment formulas vary.",
)


# ---------------------------------------------------------------------------
# 7. mortgage affordability
def _afford_py(v):
    income = float(v["income"])
    debts = float(v["debts"])
    down = float(v["down"])
    r = float(v["rate"]) / 100 / 12
    n = max(1, int(round(float(v["years"]) * 12)))
    gross_m = income / 12
    housing = min(gross_m * 0.28, gross_m * 0.36 - debts)
    housing = max(0.0, housing)
    loan = housing * (1 - (1 + r) ** -n) / r if r > 0 else housing * n
    return {"price": loan + down, "housing": housing, "loan": loan, "down": down}


AFFORDABILITY = calc(
    slug="mortgage-affordability", name="Mortgage Affordability Calculator", cat="loans",
    title="Mortgage Affordability Calculator — How Much House Can I Afford",
    desc="Estimate the home price you can afford from your income, existing debts and down "
         "payment, using the standard 28/36 debt-to-income rules lenders apply.",
    h1="How much house can I afford?",
    lede="Enter your gross income, monthly debt payments and down payment to estimate a comfortable "
         "home price and the maximum monthly housing payment.",
    fields=[num("income", "Gross annual income", 100000, unit=MONEY, pre="$", mn=10000, mx=5000000, step=1000),
            num("debts", "Other monthly debt payments", 500, unit=MONEY, pre="$", mn=0, mx=50000, step=50),
            num("down", "Down payment", 40000, unit=MONEY, pre="$", mn=0, mx=5000000, step=1000),
            num("rate", "Mortgage rate", 6.5, unit="APR %", mn=0, mx=20, step="0.01"),
            num("years", "Term", 30, unit="years", mn=5, mx=40, step=1)],
    outs=[("price", "Home price you can afford", "money0"), ("housing", "Max monthly housing payment", "money"),
          ("loan", "Mortgage amount", "money0")],
    js="""
var gross = v.income / 12;
var housing = Math.min(gross * 0.28, gross * 0.36 - v.debts);
if (housing < 0) housing = 0;
var r = v.rate / 100 / 12, n = Math.max(1, Math.round(v.years * 12));
var loan = r > 0 ? housing * (1 - Math.pow(1 + r, -n)) / r : housing * n;
return { price: loan + v.down, housing: housing, loan: loan };
""",
    py=_afford_py,
    how="""<p>Lenders do not start from the home price; they start from your income and debts. The
conventional guideline is the 28/36 rule: the housing payment (principal, interest, taxes and
insurance) should stay at or below 28% of gross monthly income, and total debt payments — housing
plus cards, cars and student loans — should stay at or below 36%. Many lenders now stretch the
back-end ratio to 43% or more, but the lower figure is the safer planning number.</p>
<p>This calculator takes the smaller of the two limits, treats it as the maximum monthly housing
payment, and works backwards to a mortgage amount and home price. Because the housing payment here
is treated as principal and interest only, leave room for property tax, insurance and any HOA
fees: reduce the result by roughly 20% for a realistic buying budget.</p>""",
    formula="""<p>Front-end test: <em>housing ≤ gross monthly income × 0.28</em>. Back-end test:
<em>housing ≤ gross monthly income × 0.36 − other monthly debts</em>. Use the smaller value as the
maximum payment, then invert the amortisation formula:</p>
<div class="fml"><code>loan = housing · (1 − (1 + r)^−n) / r
home price = loan + down payment</code></div>
<p>with <em>r</em> = APR ÷ 12 ÷ 100 and <em>n</em> = months in the term.</p>""",
    example="On a {income} income with {debts} of monthly debt and a {down} down payment, the "
            "housing cap is {housing} a month. At {rate}% over {years} years that supports a "
            "mortgage of {loan}, or a home price of about {price}.",
    mistakes=[
        "<strong>Spending the maximum.</strong> Pre-approval is a ceiling, not a budget. Daycare, "
        "commuting, repairs and savings all compete with the payment; target 25–30% of take-home pay "
        "instead.",
        "<strong>Forgetting the other house costs.</strong> Property tax, insurance, HOA dues and "
        "maintenance (budget about 1% of the home's value a year) are not in this number.",
        "<strong>Counting overtime as guaranteed income.</strong> Lenders average variable income, "
        "and a change in hours can make the payment unaffordable. Base the plan on stable salary.",
    ],
    faq=[
        ("What is a good debt-to-income ratio for a mortgage?",
         "Most lenders want a total DTI around 36% or lower, with some conventional and FHA "
         "programmes allowing up to 43–50% when compensating factors exist. Lower is safer: it "
         "leaves room for repairs and rate changes in other debts."),
        ("How much should my down payment be?",
         "20% avoids private mortgage insurance and usually earns a better rate. But 5–10% can be "
         "reasonable if it leaves you with an emergency fund; the extra cost of mortgage insurance "
         "is often smaller than the risk of being house-poor."),
        ("Does the calculator include property tax and insurance?",
         "No — it estimates the mortgage principal and interest. Property tax and homeowners "
         "insurance typically add 15–30% of the P&amp;I figure in the US, so keep that margin when "
         "deciding what to spend."),
    ],
    related=["mortgage-payment", "rent-vs-buy", "mortgage-amortization", "hourly-to-salary"],
    note="Uses the 28/36 rule; principal and interest only — taxes, insurance and HOA are extra.",
)


# ---------------------------------------------------------------------------
# 8. rent vs buy
def _rvb_py(v):
    price = float(v["price"])
    down = price * float(v["down_pct"]) / 100
    loan = price - down
    r = float(v["rate"]) / 100 / 12
    n = max(1, int(round(float(v["term"]) * 12)))
    mp = loan * r * (1 + r) ** n / ((1 + r) ** n - 1) if r > 0 else loan / n
    monthly_own = mp + price * float(v["tax_pct"]) / 100 / 12 + float(v["insurance"]) / 12 \
        + price * float(v["maint_pct"]) / 100 / 12
    years = max(1, int(round(float(v["years"]))))
    rent = float(v["rent"])
    growth = float(v["rent_growth"]) / 100
    total_rent = sum(rent * 12 * (1 + growth) ** y for y in range(years))
    # loan balance after `years` of payments
    r_ = r
    bal = loan * (1 + r_) ** (years * 12) - mp * ((1 + r_) ** (years * 12) - 1) / r_ if r_ > 0 \
        else max(0.0, loan - mp * years * 12)
    bal = max(0.0, bal)
    value = price * (1 + float(v["appr"]) / 100) ** years
    total_own = down + monthly_own * 12 * years
    net_own = total_own - (value - bal)
    return {"monthly_own": monthly_own, "monthly_rent": rent, "total_rent": total_rent,
            "net_own": net_own, "difference": net_own - total_rent}


RENT_VS_BUY = calc(
    slug="rent-vs-buy", name="Rent vs Buy Calculator", cat="loans",
    title="Rent vs Buy Calculator — Compare the True Cost of Each",
    desc="Compare the real cost of renting and buying over the same number of years, including "
         "mortgage interest, taxes, insurance, maintenance, rent increases and home equity.",
    h1="Rent vs buy calculator",
    lede="Compare what you would spend renting with what you would spend owning — including tax, "
         "insurance, maintenance, rent growth and the equity you build — over the years you plan to stay.",
    fields=[num("price", "Home price", 400000, unit=MONEY, pre="$", mn=10000, mx=20000000, step=5000),
            num("down_pct", "Down payment", 20, unit="%", mn=0, mx=100, step=1),
            num("rate", "Mortgage rate", 6.5, unit="APR %", mn=0, mx=20, step="0.01"),
            num("term", "Mortgage term", 30, unit="years", mn=5, mx=40, step=1),
            num("tax_pct", "Property tax", 1.1, unit="% of value / yr", mn=0, mx=5, step="0.05"),
            num("insurance", "Home insurance", 1800, unit="USD / yr", pre="$", mn=0, mx=50000, step=100),
            num("maint_pct", "Maintenance", 1, unit="% of value / yr", mn=0, mx=5, step="0.1"),
            num("rent", "Current rent", 2000, unit="USD / mo", pre="$", mn=0, mx=50000, step=50),
            num("rent_growth", "Annual rent increase", 3, unit="%", mn=0, mx=20, step="0.1"),
            num("appr", "Home appreciation", 3, unit="% / yr", mn=-5, mx=20, step="0.1"),
            num("years", "Years you stay", 10, unit="years", mn=1, mx=40, step=1)],
    outs=[("monthly_own", "Monthly cost to own", "money"),
          ("monthly_rent", "Monthly rent today", "money"),
          ("net_own", "Owning: total cost net of equity", "money0"),
          ("total_rent", "Renting: total paid", "money0"),
          ("difference", "Owning exceeds renting by", "money0")],
    js="""
var price=v.price, down=price*v.down_pct/100, loan=price-down;
var r=v.rate/100/12, n=Math.max(1,Math.round(v.term*12));
var mp=r>0?loan*r*Math.pow(1+r,n)/(Math.pow(1+r,n)-1):loan/n;
var own=mp+price*v.tax_pct/100/12+v.insurance/12+price*v.maint_pct/100/12;
var years=Math.max(1,Math.round(v.years)), rent=v.rent, g=v.rent_growth/100, tr=0;
for(var y=0;y<years;y++) tr+=rent*12*Math.pow(1+g,y);
var months=years*12;
var bal= r>0 ? loan*Math.pow(1+r,months)-mp*(Math.pow(1+r,months)-1)/r : loan-mp*months;
if(bal<0) bal=0;
var val=price*Math.pow(1+v.appr/100,years);
var net=down+own*12*years-(val-bal);
return {monthly_own:own,monthly_rent:rent,net_own:net,total_rent:tr,difference:net-tr};
""",
    py=_rvb_py,
    how="""<p>Rent and buy are not comparable as monthly payments alone. A mortgage payment is part
cost (interest, tax, insurance, maintenance) and part forced saving (principal). Rent is all cost,
but it buys flexibility and avoids maintenance bills. The fair comparison is total cash out over
the same period, adjusted for the equity you walk away with when you sell.</p>
<p>This calculator totals every dollar spent owning — down payment, mortgage payments, property tax,
insurance and maintenance — then subtracts the equity at the end (appreciated value minus the
remaining loan balance). For renting it totals rent with annual increases. The difference line is
the honest answer: positive means renting was cheaper over that time, negative means owning won.
Long holding periods favour buying because fixed-rate mortgage payments fall in real terms while
rent keeps rising.</p>""",
    formula="""<p>Monthly ownership cost = mortgage payment + property tax ÷ 12 + insurance ÷ 12 +
maintenance ÷ 12. Net owning cost over <em>N</em> years:</p>
<div class="fml"><code>down payment + monthly ownership × 12N − (home value − loan balance)
total rent = Σ rent × 12 × (1 + g)^y  for y = 0…N−1</code></div>
<p>The mortgage balance after <em>N</em> years comes from the amortisation formula; home value is
compounded at the appreciation rate.</p>""",
    example="On a {price} home with {down_pct}% down at {rate}%, owning costs about {monthly_own} a "
            "month in mortgage, tax, insurance and maintenance. Renting at {rent} costs "
            "{monthly_rent}. After {years} years the net cost of owning is {net_own} against "
            "{total_rent} of rent — owning is cheaper by {difference} in this scenario.",
    mistakes=[
        "<strong>Ignoring maintenance.</strong> Budget 1% of the home's value a year for repairs and "
        "upkeep. A new roof or furnace can wipe out several years of rent savings.",
        "<strong>Using short horizons.</strong> Buying usually needs five or more years just to "
        "recover closing costs and transaction fees; moving sooner often favours renting.",
        "<strong>Assuming guaranteed appreciation.</strong> Home prices can be flat or fall. Try the "
        "calculator with 0% appreciation to see how much of the case depends on that assumption.",
    ],
    faq=[
        ("Is it better to rent or buy?",
         "It depends on how long you will stay, local prices versus rents, interest rates and what "
         "else you would do with the down payment. As a rule of thumb, staying fewer than five years "
         "usually favours renting; longer stays usually favour buying, even after maintenance."),
        ("How does renting compare if I invest the difference?",
         "Renting usually costs less monthly, and investing that difference can close much of the "
         "gap over long periods. This calculator does not model investment returns on the saved "
         "money, so treat its result as the housing-only comparison."),
        ("What costs are not included?",
         "Closing costs when buying (typically 2–5% of the price) and selling costs (agent commission "
         "around 5–6% in the US) are excluded. Including them would make short holding periods look "
         "even worse for buying."),
    ],
    related=["mortgage-payment", "mortgage-affordability", "mortgage-amortization", "inflation-calculator"],
    note="Excludes closing costs, selling costs, tax deductions, HOA and investment returns on the difference.",
)


# ---------------------------------------------------------------------------
# 9. refinance break-even
def _refi_py(v):
    bal = float(v["balance"])
    old_r = float(v["old_rate"]) / 100 / 12
    old_n = max(1, int(round(float(v["old_years"]) * 12)))
    new_r = float(v["new_rate"]) / 100 / 12
    new_n = max(1, int(round(float(v["new_term"]) * 12)))
    old_m = bal * old_r * (1 + old_r) ** old_n / ((1 + old_r) ** old_n - 1) if old_r > 0 else bal / old_n
    new_m = bal * new_r * (1 + new_r) ** new_n / ((1 + new_r) ** new_n - 1) if new_r > 0 else bal / new_n
    monthly = old_m - new_m
    closing = float(v["closing"])
    old_int = old_m * old_n - bal
    new_int = new_m * new_n - bal
    if monthly <= 0:
        breakeven = "Never"
        lifetime = old_int - new_int - closing
    else:
        breakeven = f"{math_ceil(closing / monthly)} months"
        lifetime = old_int - new_int - closing
    return {"old_payment": old_m, "new_payment": new_m, "monthly": monthly,
            "breakeven": breakeven, "lifetime": lifetime}


def math_ceil(x):
    import math
    return int(math.ceil(x))


REFINANCE = calc(
    slug="refinance-breakeven", name="Refinance Break-Even Calculator", cat="loans",
    title="Refinance Break-Even Calculator — When Refinancing Pays Off",
    desc="Find the break-even point of a refinance from the new payment, closing costs and the "
         "months until the monthly savings repay the fees.",
    h1="Refinance break-even calculator",
    lede="Compare your current mortgage payment with a refinanced one, and see how many months of "
         "savings it takes to recover the closing costs.",
    fields=[num("balance", "Remaining loan balance", 250000, unit=MONEY, pre="$", mn=1000, mx=20000000, step=1000),
            num("old_rate", "Current rate", 7, unit="APR %", mn=0, mx=25, step="0.01"),
            num("old_years", "Years left on current loan", 25, unit="years", mn=1, mx=40, step=1),
            num("new_rate", "New rate", 5.5, unit="APR %", mn=0, mx=25, step="0.01"),
            num("new_term", "New loan term", 25, unit="years", mn=1, mx=40, step=1),
            num("closing", "Closing costs", 4000, unit=MONEY, pre="$", mn=0, mx=200000, step=250)],
    outs=[("monthly", "Monthly payment saving", "money"),
          ("breakeven", "Break-even time", "text"),
          ("new_payment", "New monthly payment", "money"),
          ("lifetime", "Lifetime interest saved (after costs)", "money0")],
    js="""
var bal=v.balance;
var or_=v.old_rate/100/12, on=Math.max(1,Math.round(v.old_years*12));
var nr=v.new_rate/100/12, nn=Math.max(1,Math.round(v.new_term*12));
var om=or_>0?bal*or_*Math.pow(1+or_,on)/(Math.pow(1+or_,on)-1):bal/on;
var nm=nr>0?bal*nr*Math.pow(1+nr,nn)/(Math.pow(1+nr,nn)-1):bal/nn;
var save=om-nm, be='Never';
if(save>0) be=Math.ceil(v.closing/save)+' months';
var life=(om*on-bal)-(nm*nn-bal)-v.closing;
return {old_payment:om,new_payment:nm,monthly:save,breakeven:be,lifetime:life};
""",
    py=_refi_py,
    how="""<p>Refinancing replaces one loan with another, usually to get a lower rate. It is not free:
lenders charge closing costs, typically 2–5% of the balance, and those costs are paid from savings
or rolled into the new loan. The break-even point is simply the closing cost divided by the monthly
payment saving. Stay in the home longer than that and the refinance puts you ahead; sell sooner and
you lose money.</p>
<p>A second effect is easy to miss: a refi can lower the payment by stretching the term back out.
That lowers the monthly bill but can increase total interest, because you are borrowing for longer.
The lifetime interest line here compares the remaining interest on the current loan with the total
interest on the new loan, minus the closing costs, so a “lower payment” refinance that adds years
shows up as a negative number.</p>""",
    formula="""<p>Compute both payments with the amortisation formula, then:</p>
<div class="fml"><code>monthly saving = old payment − new payment
break-even months = closing costs / monthly saving
lifetime saving = (old total interest − new total interest) − closing costs</code></div>
<p>If the new payment is higher — for example when shortening the term — the break-even is never
reached through monthly savings, but the shorter term can still reduce total interest; read the
lifetime line for that case.</p>""",
    example="Refinancing a {balance} balance from {old_rate}% with {old_years} years left to "
            "{new_rate}% over {new_term} years cuts the payment by {monthly}. With {closing} of "
            "closing costs the break-even is {breakeven}; over the full new term the interest saving "
            "after costs is {lifetime}.",
    mistakes=[
        "<strong>Comparing rates instead of payments.</strong> Points, fees and the new term all "
        "change the real comparison. Use the total interest and break-even figures.",
        "<strong>Restarting the clock.</strong> Moving a 22-year remaining balance back to 30 years "
        "lowers the payment but can raise lifetime interest sharply.",
        "<strong>Refinancing for a small saving.</strong> If closing costs are several thousand "
        "dollars and the monthly saving is $50, the break-even may be longer than you plan to stay.",
    ],
    faq=[
        ("When does refinancing make sense?",
         "When the rate drop is large enough that the monthly saving repays the closing costs well "
         "before you expect to sell, and when the new terms fit your plans. A common rule of thumb "
         "is a drop of 0.75–1% or more, but the break-even maths matters more than the rate alone."),
        ("Can I roll closing costs into the new loan?",
         "Often yes, but that raises the new balance and therefore the payment and interest. The "
         "break-even calculation here assumes costs are paid upfront; rolling them in adds a little "
         "to every payment."),
        ("Does refinancing hurt my credit score?",
         "A refinance involves a hard credit inquiry that can lower scores slightly, and the new "
         "account shortens your average account age. The effect is usually temporary, and shopping "
         "multiple lenders within a short window is treated as one inquiry by most scoring models."),
    ],
    related=["mortgage-payment", "mortgage-amortization", "loan-payment", "mortgage-affordability"],
    note="Remaining balance model. Assumes fixed rates and that closing costs are paid upfront.",
)


CALCS = [LOAN_PAYMENT, MORTGAGE_PAYMENT, AMORTIZATION, AUTO_LOAN, STUDENT_LOAN,
         CREDIT_CARD, AFFORDABILITY, RENT_VS_BUY, REFINANCE]
