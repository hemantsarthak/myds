#!/usr/bin/env python3
"""Investing calculators: compounding, savings goals, retirement, 401(k), inflation,
ROI, CAGR, APY vs APR, simple interest."""
from core import calc, num, sel, fnum

MONEY = "USD"


# ---------------------------------------------------------------------------
# 1. compound interest
def _compound_py(v):
    P = float(v["principal"])
    pmt = float(v["monthly"])
    r = float(v["rate"]) / 100 / 12
    n = max(1, int(round(float(v["years"]) * 12)))
    fv = P * (1 + r) ** n + (pmt * (((1 + r) ** n - 1) / r) if r > 0 else pmt * n)
    contrib = P + pmt * n
    return {"balance": fv, "contrib": contrib, "growth": fv - contrib}


COMPOUND = calc(
    slug="compound-interest", name="Compound Interest Calculator", cat="investing",
    title="Compound Interest Calculator — With Monthly Contributions",
    desc="See what compound interest does to a starting balance plus regular monthly "
         "contributions. Compare the money you put in with the growth it produces.",
    h1="Compound interest calculator",
    lede="Add a starting balance, a monthly contribution, an annual return and a time horizon to "
         "see how much of the final balance is money you contributed and how much is growth.",
    fields=[num("principal", "Starting balance", 10000, unit=MONEY, pre="$", mn=0, mx=100000000, step=500),
            num("monthly", "Monthly contribution", 500, unit="USD / mo", pre="$", mn=0, mx=1000000, step=50),
            num("rate", "Annual return", 7, unit="%", mn=0, mx=40, step="0.1"),
            num("years", "Years invested", 10, unit="years", mn=1, mx=60, step=1)],
    outs=[("balance", "Future balance", "money0"),
          ("contrib", "Total contributed", "money0"),
          ("growth", "Growth earned", "money0")],
    viz=[("Contributed", "contrib", "money0"), ("Growth", "growth", "money0")],
    js="""
var P=v.principal, pmt=v.monthly, r=v.rate/100/12, n=Math.max(1,Math.round(v.years*12));
var fv=P*Math.pow(1+r,n)+(r>0?pmt*((Math.pow(1+r,n)-1)/r):pmt*n);
var contrib=P+pmt*n;
return {balance:fv,contrib:contrib,growth:fv-contrib};
""",
    py=_compound_py,
    how="""<p>Compound interest means the interest you earn starts earning interest too. With monthly
compounding, each month's return is added to the balance and the next month compounds on the new,
larger amount. Over long periods that snowball does most of the work: the contributions line grows
in a straight line, while the growth line curves upwards.</p>
<p>The monthly contribution is what makes the curve steep. Contributions are added at the end of
each month in this model, which is slightly conservative compared with contributing at the start of
the month. The annual return is treated as a constant rate — real markets do not deliver a smooth
7% every year, so treat the result as an average-case projection, not a promise.</p>""",
    formula="""<p>With monthly rate <em>r</em> = annual return ÷ 12 ÷ 100, <em>n</em> months and
monthly contribution <em>C</em>:</p>
<div class="fml"><code>future value = P · (1 + r)^n  +  C · ((1 + r)^n − 1) / r</code></div>
<p>The first term compounds the starting balance; the second is the future value of an ordinary
annuity, i.e. the monthly contributions. Contributions are <em>P + C × n</em> and growth is the
difference.</p>""",
    example="Starting with {principal} and adding {monthly} a month at {rate}% for {years} years "
            "produces a balance of {balance}. You contributed {contrib} of that; the remaining "
            "{growth} is compound growth.",
    mistakes=[
        "<strong>Using an average return as a guarantee.</strong> A 7% average can include long "
        "stretches of losses. Projection tools answer “what if”, not “what will happen”.",
        "<strong>Forgetting fees.</strong> A 1% annual fee on a 7% return removes about 14% of the "
        "final balance over 30 years because it compounds against you too.",
        "<strong>Ignoring inflation.</strong> Nominal growth is not purchasing power. At 3% "
        "inflation, a balance that looks like it doubled buys about 40% less than it appears.",
    ],
    faq=[
        ("How often should interest compound?",
         "More frequent compounding produces a slightly higher effective return for the same stated "
         "rate. The difference between monthly and daily compounding is small; the bigger levers "
         "are the rate, the time and the contribution amount."),
        ("What return should I assume?",
         "For a diversified equity-heavy portfolio, many planners use 5–7% real (after inflation) "
         "for long horizons. For savings accounts, use the account's actual APY. Showing two "
         "scenarios — conservative and optimistic — is usually more useful than one number."),
        ("Are contributions made at the start or end of the month?",
         "This calculator assumes the end of each month, which matches most payroll and automatic "
         "investment schedules. Starting-of-month contributions would produce a slightly higher "
         "balance — roughly one extra month of return on each contribution."),
    ],
    related=["savings-goal", "retirement-nest-egg", "401k-growth", "inflation-calculator"],
    note="Assumes a constant annual return compounded monthly; contributions at month end.",
)


# ---------------------------------------------------------------------------
# 2. savings goal
def _savings_py(v):
    goal = float(v["goal"])
    bal = float(v["current"])
    pmt = float(v["monthly"])
    r = float(v["rate"]) / 100 / 12
    if bal >= goal:
        return {"months": "Already reached", "years": 0.0, "contrib": 0.0, "interest": 0.0}
    m = 0
    interest = 0.0
    while bal < goal and m < 1200:
        i = bal * r
        interest += i
        bal = bal + i + pmt
        m += 1
    if bal < goal:
        return {"months": "Over 100 years", "years": 0.0, "contrib": float(v["current"]) + pmt * m,
                "interest": interest}
    return {"months": f"{m} months", "years": m / 12, "contrib": float(v["current"]) + pmt * m,
            "interest": interest}


SAVINGS_GOAL = calc(
    slug="savings-goal", name="Savings Goal Calculator", cat="investing",
    title="Savings Goal Calculator — How Long to Reach Your Target",
    desc="Find out how many months it takes to reach a savings target from your current balance, "
         "monthly deposits and interest rate — and how much of it is interest.",
    h1="Savings goal calculator",
    lede="Enter a target amount, what you already have and what you can save each month to see how "
         "long the goal takes and how much of it comes from interest.",
    fields=[num("goal", "Savings goal", 20000, unit=MONEY, pre="$", mn=100, mx=10000000, step=500),
            num("current", "Current savings", 2000, unit=MONEY, pre="$", mn=0, mx=10000000, step=500),
            num("monthly", "Monthly savings", 300, unit="USD / mo", pre="$", mn=0, mx=1000000, step=25),
            num("rate", "Interest / return rate", 4, unit="APY %", mn=0, mx=30, step="0.1")],
    outs=[("months", "Time to reach goal", "text"), ("contrib", "Total saved (deposits)", "money0"),
          ("interest", "Interest earned", "money0")],
    js="""
var goal=v.goal, bal=v.current, pmt=v.monthly, r=v.rate/100/12;
if (bal >= goal) return {months:'Already reached',contrib:0,interest:0};
var m=0, interest=0;
while (bal < goal && m < 1200) { var i=bal*r; interest+=i; bal=bal+i+pmt; m+=1; }
if (bal < goal) return {months:'Over 100 years',contrib:v.current+pmt*m,interest:interest};
return {months:m+' months',contrib:v.current+pmt*m,interest:interest};
""",
    py=_savings_py,
    how="""<p>Reaching a savings goal is mostly arithmetic: each month the balance earns interest, then
your deposit is added. Interest is earned on the whole balance, so the earlier you start and the
higher the rate, the fewer months the goal takes. The loop stops on the first month where the
balance meets or exceeds the target.</p>
<p>For an emergency fund the rate is usually a high-yield savings account, where 4–5% APY is
possible but changes with central-bank rates. For a longer-term goal held in investments, a return
figure is an assumption rather than a guarantee — try 4% and 7% to see how sensitive the timeline
is. The tool also flags the two failure cases: a goal already met, and a deposit so small relative
to the target that it takes more than a century.</p>""",
    formula="""<p>Iterate monthly: <em>balance ← balance × (1 + r) + deposit</em>, where
<em>r</em> = APY ÷ 12 ÷ 100, until <em>balance ≥ goal</em>. Total deposits are
<em>current savings + monthly deposit × months</em>; interest is the difference between the
balance and the deposits. For a fixed timeline there is a closed-form annuity formula, but for
“how long?” the loop is the clearest way to solve it.</p>""",
    example="To reach {goal} starting from {current} and saving {monthly} a month at {rate}% takes "
            "{months}. By then you will have deposited {contrib}; the other {interest} comes from "
            "interest along the way.",
    mistakes=[
        "<strong>Leaving the emergency fund in a 0.1% account.</strong> The rate matters less than "
        "actually saving, but moving from 0.1% to 4% APY can shorten a multi-year goal by months.",
        "<strong>Not adjusting the goal for inflation.</strong> A house deposit or car target in "
        "five years costs more than the number typed today. Add 2–4% a year to the target.",
        "<strong>Counting transfers as progress.</strong> Money moved from checking to savings is "
        "saving; money spent from savings is not. Track the net balance, not just deposits.",
    ],
    faq=[
        ("How much should I save each month?",
         "A common starting point is 20% of take-home pay, split between emergency fund, retirement "
         "and specific goals. If the calculator says a goal takes too long, either raise the monthly "
         "amount, extend the deadline or lower the target — there is no fourth option."),
        ("Should I use a savings account or investments for a goal?",
         "Keep money needed within about three years in cash or short-term deposits: investments can "
         "fall exactly when the bill arrives. Longer goals can accept more volatility in exchange "
         "for a higher expected return."),
        ("What if my bank pays interest monthly instead of annually?",
         "The difference is small. This calculator converts an annual rate to a monthly rate, which "
         "matches monthly crediting closely enough for planning; use the account's APY to be precise."),
    ],
    related=["compound-interest", "retirement-nest-egg", "inflation-calculator", "loan-payment"],
    note="Assumes the rate is constant and deposits are made at the end of each month.",
)


# ---------------------------------------------------------------------------
# 3. retirement nest egg
def _retirement_py(v):
    age = int(round(float(v["age"])))
    retire = int(round(float(v["retire_age"])))
    years = max(1, retire - age)
    r = float(v["rate"]) / 100 / 12
    n = years * 12
    P = float(v["current"])
    pmt = float(v["monthly"])
    fv = P * (1 + r) ** n + (pmt * (((1 + r) ** n - 1) / r) if r > 0 else pmt * n)
    contrib = P + pmt * n
    real = fv / (1 + float(v["inflation"]) / 100) ** years
    return {"balance": fv, "real": real, "income": fv * 0.04 / 12, "contrib": contrib}


RETIREMENT = calc(
    slug="retirement-nest-egg", name="Retirement Nest Egg Calculator", cat="investing",
    title="Retirement Nest Egg Calculator — How Much Will I Have",
    desc="Project your retirement balance from current savings, monthly contributions, expected "
         "returns and years to retirement. See the real value and a 4% rule income estimate.",
    h1="Retirement nest egg calculator",
    lede="Project the retirement balance you are on track for, what it is worth in today's money, "
         "and the monthly income a 4% withdrawal rate could support.",
    fields=[num("age", "Current age", 30, unit="years", mn=15, mx=80, step=1),
            num("retire_age", "Retirement age", 65, unit="years", mn=30, mx=90, step=1),
            num("current", "Current retirement savings", 30000, unit=MONEY, pre="$", mn=0, mx=10000000, step=1000),
            num("monthly", "Monthly contribution", 500, unit="USD / mo", pre="$", mn=0, mx=100000, step=50),
            num("rate", "Expected annual return", 7, unit="%", mn=0, mx=20, step="0.1"),
            num("inflation", "Expected inflation", 2.5, unit="%", mn=0, mx=15, step="0.1")],
    outs=[("balance", "Projected balance at retirement", "money0"),
          ("real", "In today's money", "money0"),
          ("income", "Sustainable monthly income (4% rule)", "money0"),
          ("contrib", "Total you contribute", "money0")],
    js="""
var years=Math.max(1,Math.round(v.retire_age-v.age)), r=v.rate/100/12, n=years*12;
var fv=v.current*Math.pow(1+r,n)+(r>0?v.monthly*((Math.pow(1+r,n)-1)/r):v.monthly*n);
var real=fv/Math.pow(1+v.inflation/100,years);
return {balance:fv,real:real,income:fv*0.04/12,contrib:v.current+v.monthly*n};
""",
    py=_retirement_py,
    how="""<p>This projection compounds your current savings and monthly contributions at a constant
annual return until your retirement age. It is the same maths as the compound interest calculator,
with a retirement framing. The “in today's money” line divides the nominal balance by cumulative
inflation, which is the number to compare with today's prices when judging whether the nest egg
feels adequate.</p>
<p>The income estimate applies the 4% rule: withdraw 4% of the balance in the first year, then
increase that amount with inflation each year. It is a planning heuristic from US historical
returns, not a guarantee, and it assumes a diversified portfolio and a 25–30 year retirement. If
you plan a longer retirement or want more certainty, use 3–3.5% instead.</p>""",
    formula="""<p>With <em>r</em> = return ÷ 12 ÷ 100, <em>n</em> = (retirement age − current age) × 12:</p>
<div class="fml"><code>balance = P · (1 + r)^n + C · ((1 + r)^n − 1) / r
real value = balance / (1 + inflation)^years
safe monthly income ≈ balance × 0.04 / 12</code></div>
<p>Contributions total <em>P + C × n</em>; everything above that is investment growth.</p>""",
    example="From age {age} to {retire_age}, starting at {current} and adding {monthly} a month at "
            "{rate}% produces {balance} by retirement. Adjusted for {inflation}% inflation that is "
            "about {real} in today's money, supporting roughly {income} a month under the 4% rule.",
    mistakes=[
        "<strong>Forgetting employer contributions.</strong> A 401(k) match can add thousands a year. "
        "Add it to the monthly contribution, or use the dedicated 401(k) calculator.",
        "<strong>Using nominal numbers to judge adequacy.</strong> A million dollars in 40 years is "
        "not a million dollars today. Always check the inflation-adjusted line.",
        "<strong>Retiring with no cash buffer.</strong> The 4% rule assumes you can sell assets in a "
        "downturn without touching the core portfolio. Real retirements need 1–2 years of spending "
        "in cash to avoid selling at the bottom.",
    ],
    faq=[
        ("How much do I need to retire?",
         "A rough target is 25 times your annual spending, which is the inverse of the 4% rule. If "
         "you want to spend $60,000 a year, the target is about $1.5 million in today's money; "
         "Social Security or a pension reduces the amount the portfolio must cover."),
        ("What return should I assume before retirement?",
         "Long-run diversified portfolios have historically returned around 6–8% nominal, but the "
         "next decades may differ. Planning with 5–6% nominal is conservative and reduces the chance "
         "of a shortfall."),
        ("Does this include taxes?",
         "No. Traditional 401(k) and IRA withdrawals are taxed as income, so the sustainable income "
         "figure here is pre-tax. Tax-advantaged accounts such as a Roth IRA behave differently."),
    ],
    related=["401k-growth", "compound-interest", "inflation-calculator", "savings-goal"],
    note="Constant returns; 4% rule income is pre-tax and not a guarantee.",
)


# ---------------------------------------------------------------------------
# 4. 401(k) growth
def _k401_py(v):
    sal = float(v["salary"])
    rate = float(v["return_rate"]) / 100 / 12
    n = max(1, int(round(float(v["years"]) * 12)))
    ee = sal * float(v["contribution"]) / 100 / 12
    er = min(float(v["contribution"]), float(v["match_cap"])) / 100 * sal * float(v["match"]) / 100 / 12
    bal = float(v["current"])
    fv = bal * (1 + rate) ** n + ((ee + er) * (((1 + rate) ** n - 1) / rate) if rate > 0 else (ee + er) * n)
    contrib = bal + (ee + er) * n
    return {"balance": fv, "contrib": contrib, "growth": fv - contrib, "employer": er * n}


K401 = calc(
    slug="401k-growth", name="401(k) Growth Calculator", cat="investing",
    title="401(k) Growth Calculator — With Employer Match",
    desc="Project your 401(k) balance including employer matching contributions. See what the "
         "match is worth and how much of the balance is growth.",
    h1="401(k) growth calculator",
    lede="Project a 401(k) balance from your salary, contribution rate, employer match and expected "
         "return — and see how much of the total comes from the match and from growth.",
    fields=[num("salary", "Annual salary", 80000, unit=MONEY, pre="$", mn=10000, mx=2000000, step=1000),
            num("contribution", "Your contribution", 6, unit="% of salary", mn=0, mx=100, step="0.5"),
            num("match", "Employer match", 50, unit="% of your contribution", mn=0, mx=200, step=5),
            num("match_cap", "Match applies up to", 6, unit="% of salary", mn=0, mx=100, step="0.5"),
            num("current", "Current 401(k) balance", 10000, unit=MONEY, pre="$", mn=0, mx=10000000, step=1000),
            num("return_rate", "Expected annual return", 7, unit="%", mn=0, mx=20, step="0.1"),
            num("years", "Years until retirement", 30, unit="years", mn=1, mx=50, step=1)],
    outs=[("balance", "Projected 401(k) balance", "money0"),
          ("contrib", "Total contributions (yours + employer)", "money0"),
          ("growth", "Investment growth", "money0"),
          ("employer", "Employer match money", "money0")],
    js="""
var sal=v.salary, r=v.return_rate/100/12, n=Math.max(1,Math.round(v.years*12));
var ee=sal*v.contribution/100/12;
var er=Math.min(v.contribution,v.match_cap)/100*sal*v.match/100/12;
var fv=v.current*Math.pow(1+r,n)+(r>0?(ee+er)*((Math.pow(1+r,n)-1)/r):(ee+er)*n);
var contrib=v.current+(ee+er)*n;
return {balance:fv,contrib:contrib,growth:fv-contrib,employer:er*n};
""",
    py=_k401_py,
    how="""<p>A 401(k) grows from three sources: your own contributions, your employer's match and
investment returns. The match is the highest-risk-free return most people ever get access to — a
50% match on the first 6% of salary is an instant 50% gain on that money, before any market return.
Not contributing at least to the match is leaving compensation on the table.</p>
<p>The projection assumes contributions are made monthly and the salary stays constant. Real
salaries rise, so the actual balance is usually higher; the model also ignores plan fees, vesting
schedules (employer money you lose if you leave early) and annual contribution limits. It is
pre-tax money in a traditional 401(k), so withdrawals in retirement are taxed as income.</p>""",
    formula="""<p>Monthly employee contribution = salary × contribution% ÷ 12. Monthly employer
contribution = min(contribution%, match cap%) × salary × match% ÷ 12, i.e. the match only applies
up to the cap.</p>
<div class="fml"><code>balance = B · (1 + r)^n + (employee + employer) · ((1 + r)^n − 1) / r</code></div>
<p>where <em>r</em> = return ÷ 12 ÷ 100 and <em>n</em> = years × 12. The employer match total is
the monthly employer contribution × <em>n</em>.</p>""",
    example="On a {salary} salary, contributing {contribution}% with a {match}% match up to "
            "{match_cap}%, the monthly employer contribution matters: over {years} years at {rate}% "
            "the balance reaches {balance}. Of that, {contrib} is contributions and {growth} is "
            "growth, with {employer} coming directly from the employer match.",
    mistakes=[
        "<strong>Stopping at the match.</strong> The match is the minimum, not the target. Most "
        "planners suggest 15% of gross pay including the match for a comfortable retirement.",
        "<strong>Ignoring the expense ratio.</strong> A 1% fund fee versus 0.05% index funds can "
        "cost a third of the final balance over 30 years.",
        "<strong>Cashing out when changing jobs.</strong> A cash-out triggers income tax plus a 10% "
        "early-withdrawal penalty in the US and permanently loses the growth. Roll it over instead.",
    ],
    faq=[
        ("How much should I contribute to my 401(k)?",
         "At minimum, enough to capture the full employer match. A common target is 15% of gross "
         "income including the match, rising towards the annual contribution limit as income grows."),
        ("What is vesting?",
         "Vesting is the schedule on which employer contributions become yours. Many plans vest over "
         "three to six years; if you leave earlier you may forfeit part of the employer money. Your "
         "own contributions are always yours."),
        ("Is a 401(k) better than an IRA?",
         "Use the 401(k) first if it offers a match, then compare fees and fund choices. IRAs often "
         "have broader investment options, while 401(k)s allow much higher annual contributions."),
    ],
    related=["retirement-nest-egg", "compound-interest", "paycheck-net", "inflation-calculator"],
    note="Constant salary and return; ignores plan fees, vesting and annual contribution limits.",
)


# ---------------------------------------------------------------------------
# 5. inflation
def _inflation_py(v):
    amt = float(v["amount"])
    r = float(v["rate"]) / 100
    years = float(v["years"])
    future = amt * (1 + r) ** years
    power = amt / (1 + r) ** years
    return {"future_cost": future, "purchasing_power": power, "loss": (1 - 1 / (1 + r) ** years) * 100}


INFLATION = calc(
    slug="inflation-calculator", name="Inflation Calculator", cat="investing",
    title="Inflation Calculator — Future Cost & Purchasing Power",
    desc="See what inflation does to prices and to the value of your money over time. Calculate the "
         "future cost of a basket of goods and the purchasing power of today's dollars.",
    h1="Inflation calculator",
    lede="Find out what today's amount will cost in the future, and what future money is really "
         "worth in today's prices, at a constant rate of inflation.",
    fields=[num("amount", "Amount today", 1000, unit=MONEY, pre="$", mn=1, mx=100000000, step=100),
            num("rate", "Annual inflation rate", 3, unit="%", mn=0, mx=30, step="0.1"),
            num("years", "Number of years", 10, unit="years", mn=0, mx=80, step=1)],
    outs=[("future_cost", "Same basket will cost", "money"),
          ("purchasing_power", "Today's amount is worth (in today's money)", "money"),
          ("loss", "Purchasing power lost", "pct1")],
    js="""
var r=v.rate/100, y=v.years;
return {future_cost:v.amount*Math.pow(1+r,y),
        purchasing_power:v.amount/Math.pow(1+r,y),
        loss:(1-1/Math.pow(1+r,y))*100};
""",
    py=_inflation_py,
    how="""<p>Inflation erodes purchasing power. If prices rise by 3% a year, something that costs
$1,000 today costs about $1,344 in ten years, while $1,000 set aside in a drawer in ten years buys
only about $744 of today's goods. Both directions matter: the first for planning future expenses,
the second for judging whether a savings balance is really growing.</p>
<p>This calculator uses a constant inflation rate, which is a simplification — real inflation
varies year to year and differs sharply by spending category. Housing, healthcare and education
have historically risen faster than the headline figure, while electronics and clothing have often
fallen. For a retirement or education plan, a slightly higher rate for the relevant category is
more conservative than the general rate.</p>""",
    formula="""<p>Future cost of a fixed basket = <em>amount × (1 + i)^years</em>. Purchasing power of
a fixed amount = <em>amount ÷ (1 + i)^years</em>. Purchasing-power loss is
<em>1 − 1/(1 + i)^years</em>.</p>
<div class="fml"><code>future cost  = A · (1 + i)^y
real value   = A / (1 + i)^y</code></div>
<p>The two are not independent: at 3% for 10 years, costs rise 34.4% and purchasing power falls
25.6% — the same fact expressed two ways.</p>""",
    example="At {rate}% inflation, {amount} today becomes {future_cost} of spending in {years} "
            "years. Put the other way, {amount} held as cash in {years} years would buy only "
            "{purchasing_power} of what it buys today — a {loss} loss of purchasing power.",
    mistakes=[
        "<strong>Forgetting inflation when planning retirement.</strong> A spending need of $60,000 "
        "today is roughly $120,000 in 30 years at 2.5% inflation. Plan in today's money and then "
        "adjust once.",
        "<strong>Treating cash as risk-free.</strong> A savings account paying less than inflation "
        "loses purchasing power every year, even though the nominal balance rises.",
        "<strong>Using one rate for every category.</strong> Healthcare and education have "
        "historically outpaced headline CPI. Use category-specific rates for long-term goals.",
    ],
    faq=[
        ("What is a normal inflation rate?",
         "Major central banks target about 2% a year, and long-run US CPI has averaged roughly 3%. "
         "Recent years have shown both very low and unusually high rates, which is why planning "
         "with a range rather than a single number is safer."),
        ("How do I protect savings from inflation?",
         "In the short term, higher-yield savings accounts and inflation-linked bonds help. Over "
         "long periods, equities and real assets have historically outpaced inflation, though with "
         "much more volatility."),
        ("Is inflation the same as a price increase?",
         "Inflation is the average increase across a basket of goods and services. Individual "
         "prices can rise faster or slower, and some fall. Your personal inflation rate depends on "
         "what you actually spend money on."),
    ],
    related=["compound-interest", "retirement-nest-egg", "roi-calculator", "savings-goal"],
    note="Constant inflation rate; not a CPI series or a forecast.",
)


# ---------------------------------------------------------------------------
# 6. ROI
def _roi_py(v):
    initial = float(v["initial"])
    final = float(v["final"])
    years = float(v["years"])
    profit = final - initial
    roi = profit / initial * 100 if initial else 0.0
    annualised = ((final / initial) ** (1 / years) - 1) * 100 if initial > 0 and years > 0 else 0.0
    return {"roi": roi, "profit": profit, "annualised": annualised}


ROI = calc(
    slug="roi-calculator", name="ROI Calculator", cat="investing",
    title="ROI Calculator — Return on Investment & Annualised Return",
    desc="Calculate return on investment, net profit and the equivalent annualised return for any "
         "investment or project. Compare deals on a like-for-like basis.",
    h1="Return on investment (ROI) calculator",
    lede="Enter what you put in, what you got back and how long it took to see total ROI, profit and "
         "the annualised return.",
    fields=[num("initial", "Amount invested", 5000, unit=MONEY, pre="$", mn=1, mx=100000000, step=100),
            num("final", "Value now / amount returned", 8000, unit=MONEY, pre="$", mn=0, mx=100000000, step=100),
            num("years", "Holding period", 5, unit="years", mn=0.1, mx=80, step="0.1")],
    outs=[("roi", "Total return on investment", "pct"),
          ("profit", "Net profit", "money"),
          ("annualised", "Annualised return (CAGR)", "pct")],
    js="""
var initial=v.initial, fin=v["final"], years=v.years;
var profit=fin-initial;
var roi=initial?profit/initial*100:0;
var annual=initial>0&&years>0?(Math.pow(fin/initial,1/years)-1)*100:0;
return {roi:roi,profit:profit,annualised:annual};
""",
    py=_roi_py,
    how="""<p>Return on investment compares the profit with the amount invested: a $5,000 investment
worth $8,000 has a $3,000 profit and a 60% ROI. That figure is easy to understand but hard to
compare — 60% over five years is a very different result from 60% over five months. The annualised
return (compound annual growth rate) puts every investment on the same per-year scale, which is why
professionals use it.</p>
<p>The calculator assumes no additional money went in or out during the period and that the final
value includes any dividends or income received. For a project rather than a market investment, use
the total cost as “amount invested” and the total revenue as “amount returned”. Negative results are
possible: if the final value is below the initial amount, both ROI and the annualised return come
out negative.</p>""",
    formula="""<p>Total ROI = <em>(final − initial) ÷ initial × 100</em>. Annualised return
(CAGR) = <em>(final ÷ initial)^(1/years) − 1</em>.</p>
<div class="fml"><code>ROI  = (V_final − V_initial) / V_initial × 100%
CAGR = (V_final / V_initial)^(1 / years) − 1</code></div>
<p>CAGR is the constant annual rate that would turn the starting amount into the ending amount over
the period. It smooths out year-to-year volatility, which is both its strength and its limitation.</p>""",
    example="Investing {initial} and ending with {final} after {years} years gives a total return of "
            "{roi}, a profit of {profit}, and an annualised return of {annualised} a year.",
    mistakes=[
        "<strong>Ignoring the time period.</strong> 60% over one year and 60% over ten years are "
        "opposite ends of the spectrum, but the plain ROI number looks identical.",
        "<strong>Leaving out costs.</strong> Fees, commissions and taxes reduce the real return. "
        "Use the net amount you actually received as the final value.",
        "<strong>Comparing CAGR with simple average returns.</strong> If an investment returns +50% "
        "then −50%, the average annual return is 0% but the money is down 25%. CAGR captures the "
        "compounding reality; arithmetic averages do not.",
    ],
    faq=[
        ("What is a good ROI?",
         "It depends entirely on risk and time. A risk-free savings account might return 4% a year, "
         "a diversified equity portfolio has historically averaged 7–10% nominal, and a small "
         "business might target 20%+. Compare against the risk you are taking, not just the number."),
        ("What is the difference between ROI and CAGR?",
         "ROI is total profit as a percentage of the amount invested, regardless of time. CAGR is "
         "the equivalent constant annual growth rate. Use ROI for a quick comparison of similar "
         "deals and CAGR to compare investments held for different lengths of time."),
        ("Can ROI be negative?",
         "Yes. If the final value is below the amount invested, the ROI is negative and represents "
         "a loss. The formula handles it automatically; the annualised return turns negative too."),
    ],
    related=["cagr-calculator", "compound-interest", "inflation-calculator", "simple-interest"],
    note="No cash flows in or out during the period; final value is net of costs and dividends received.",
)


# ---------------------------------------------------------------------------
# 7. CAGR
def _cagr_py(v):
    begin = float(v["begin"])
    end = float(v["end"])
    years = float(v["years"])
    multiple = end / begin if begin else 0.0
    total = (multiple - 1) * 100
    cagr = (multiple ** (1 / years) - 1) * 100 if multiple > 0 else -100.0
    return {"cagr": cagr, "total": total, "multiple": multiple}


CAGR = calc(
    slug="cagr-calculator", name="CAGR Calculator", cat="investing",
    title="CAGR Calculator — Compound Annual Growth Rate",
    desc="Calculate compound annual growth rate from a starting value, ending value and number of "
         "years. Compare investments held for different periods fairly.",
    h1="CAGR calculator",
    lede="Turn a starting value, ending value and time period into a compound annual growth rate — "
         "the single yearly number that describes the whole period.",
    fields=[num("begin", "Beginning value", 10000, unit=MONEY, pre="$", mn=1, mx=100000000, step=500),
            num("end", "Ending value", 20000, unit=MONEY, pre="$", mn=0, mx=100000000, step=500),
            num("years", "Number of years", 5, unit="years", mn=0.1, mx=100, step="0.1")],
    outs=[("cagr", "Compound annual growth rate", "pct"),
          ("total", "Total growth", "pct"),
          ("multiple", "Growth multiple", "num1")],
    js="""
var b=v.begin, e=v["end"], y=v.years;
var mult=b?e/b:0;
return {cagr:mult>0?(Math.pow(mult,1/y)-1)*100:-100,
        total:(mult-1)*100, multiple:mult};
""",
    py=_cagr_py,
    how="""<p>CAGR answers a simple question: what constant yearly percentage would turn the starting
value into the ending value? It is calculated from the total change over the period, not from the
individual yearly returns, so it is a summary — not a prediction. Two investments with the same
starting and ending values have the same CAGR even if one went up smoothly and the other crashed
and recovered.</p>
<p>Because it is a geometric average, CAGR is much fairer than averaging yearly percentage returns.
It is the standard way to compare funds, companies and portfolios held for different lengths of
time. A negative result simply means the ending value is below the starting value. If the beginning
value is zero the ratio is undefined, and if the ending value is zero the CAGR is −100%.</p>""",
    formula="""<p>For beginning value <em>B</em>, ending value <em>E</em> and <em>y</em> years:</p>
<div class="fml"><code>CAGR = (E / B)^(1 / y) − 1</code></div>
<p>Expressed as a percentage, multiply by 100. The total growth multiple is <em>E ÷ B</em> and total
growth is <em>(E ÷ B − 1) × 100%</em>. Rearranged, this is exactly the compound interest formula:
<em>E = B × (1 + CAGR)^y</em>.</p>""",
    example="Growing from {begin} to {end} over {years} years is a total gain of {total} and a "
            "multiple of {multiple}×. The equivalent compound annual growth rate is {cagr} a year.",
    mistakes=[
        "<strong>Averaging annual returns.</strong> Taking the arithmetic mean of yearly percentage "
        "returns always overstates compound growth when returns vary.",
        "<strong>Using it on volatile short periods.</strong> A two-year CAGR from a market bottom "
        "to a peak can look spectacular and tells you nothing about the future.",
        "<strong>Ignoring contributions.</strong> If you added money during the period, the "
        "beginning and ending values do not describe the same investment. Use a time-weighted "
        "return for portfolios with deposits."
    ],
    faq=[
        ("What is a good CAGR?",
         "For long-term equity portfolios, 7–10% nominal is a reasonable historical benchmark; a "
         "savings account might deliver 3–5%. A high CAGR over a short period is easier to achieve "
         "by luck than a moderate one over decades."),
        ("How is CAGR different from average annual return?",
         "CAGR compounds; a simple average does not. If an investment gains 100% one year and loses "
         "50% the next, the arithmetic average is +25% while the actual compound growth rate is 0%."),
        ("Can CAGR be calculated monthly?",
         "Yes, with the same formula using months instead of years. The result is a compound monthly "
         "growth rate; multiply the period consistently — the exponent must use the same time unit "
         "as the answer you want."),
    ],
    related=["roi-calculator", "compound-interest", "inflation-calculator", "retirement-nest-egg"],
    note="No cash flows in or out during the period; values are net of costs.",
)


# ---------------------------------------------------------------------------
# 8. APY vs APR
def _apy_py(v):
    apr = float(v["apr"])
    n = float(v["freq"])
    apy = ((1 + apr / 100 / n) ** n - 1) * 100
    principal = float(v["principal"])
    return {"apy": apy, "interest": principal * apy / 100,
            "periodic": apr / n, "extra": principal * (apy - apr) / 100}


APY = calc(
    slug="apy-vs-apr", name="APY vs APR Calculator", cat="investing",
    title="APY vs APR Calculator — Effective Annual Yield",
    desc="Convert a nominal APR into the effective annual rate (APY) for any compounding "
         "frequency, and see what the difference is worth on a real balance.",
    h1="APY vs APR calculator",
    lede="Enter a nominal annual rate and how often it compounds to get the effective annual yield "
         "(APY) and the extra interest compounding produces.",
    fields=[num("apr", "Nominal annual rate (APR)", 5, unit="%", mn=0, mx=100, step="0.01"),
            sel("freq", "Compounding frequency",
                [("12", "Monthly"), ("4", "Quarterly"), ("365", "Daily"), ("1", "Annually")], "12"),
            num("principal", "Balance", 10000, unit=MONEY, pre="$", mn=1, mx=10000000, step=1000)],
    outs=[("apy", "Effective annual rate (APY)", "pct"),
          ("interest", "Interest earned in a year", "money"),
          ("periodic", "Rate per compounding period", "pct"),
          ("extra", "Extra vs simple annual rate", "money")],
    js="""
var n=Number(v.freq), apr=v.apr, principal=v.principal;
var apy=(Math.pow(1+apr/100/n,n)-1)*100;
return {apy:apy, interest:principal*apy/100, periodic:apr/n,
        extra:principal*(apy-apr)/100};
""",
    py=_apy_py,
    how="""<p>APR and APY both describe an annual rate, but they count compounding differently. APR is
the nominal rate — the number a bank quotes before compounding. APY, also called the effective
annual rate, includes the effect of interest being added to the balance during the year and
compounding. For the same nominal APR, more frequent compounding gives a higher APY.</p>
<p>The gap is tiny at low rates and grows with the rate: 5% compounded daily is 5.13% APY, while
20% compounded daily is 22.13% APY. That is why comparing savings accounts and loans on APY rather
than APR is fairer — APY is what you actually earn or pay over a year. Note that banks may quote a
daily rate without compounding; this calculator assumes the quoted rate compounds at the selected
frequency, which is the standard APY definition.</p>""",
    formula="""<p>For nominal annual rate <em>a</em> (as a decimal) compounded <em>n</em> times a
year:</p>
<div class="fml"><code>APY = (1 + a / n)^n − 1</code></div>
<p>The interest earned on balance <em>P</em> is <em>P × APY</em>. The rate for each compounding
period is <em>a / n</em>. In the limit of continuous compounding, APY becomes
<em>e^a − 1</em>.</p>""",
    example="A nominal {apr}% rate compounded monthly has an effective annual rate of {apy}. On a "
            "{principal} balance that is {interest} of interest in the year — {extra} more than the "
            "nominal rate would suggest.",
    mistakes=[
        "<strong>Comparing APR on a savings account with APY.</strong> The APY always looks "
        "slightly higher because it includes compounding. Compare like with like.",
        "<strong>Assuming APR is the true cost of a loan.</strong> For loans, APR includes most "
        "fees, so it is usually higher than the interest rate but lower than the rate you actually "
        "pay if you pay early or make minimum payments.",
        "<strong>Ignoring compounding frequency in long-term projections.</strong> The difference "
        "compounds too: over 30 years, monthly versus annual compounding is worth several percent "
        "of the final balance."
    ],
    faq=[
        ("What is the difference between APR and APY?",
         "APR is the nominal annual rate without accounting for intra-year compounding; APY includes "
         "it. For money you earn, APY is the relevant number; for money you borrow, the APR (which "
         "also includes fees) is the comparable figure."),
        ("Which is better for savings, high APY or high APR?",
         "For savings accounts, only the APY matters — it is what you actually earn. APR is the "
         "payment-rate quote used for loans, not usually for deposit accounts."),
        ("Does compounding frequency really matter?",
         "At typical rates the difference is small: 5% compounded monthly is 5.12% APY, daily is "
         "5.13%. At higher rates the gap widens, and over long periods even small differences "
         "compound into meaningful amounts."),
    ],
    related=["compound-interest", "simple-interest", "savings-goal", "inflation-calculator"],
    note="Uses the standard APY definition: nominal rate compounded at the selected frequency.",
)


# ---------------------------------------------------------------------------
# 9. simple interest
def _simple_py(v):
    P = float(v["principal"])
    r = float(v["rate"]) / 100
    years = float(v["years"])
    interest = P * r * years
    return {"interest": interest, "total": P + interest, "monthly": P * r / 12}


SIMPLE = calc(
    slug="simple-interest", name="Simple Interest Calculator", cat="investing",
    title="Simple Interest Calculator — Interest, Total and Monthly",
    desc="Calculate simple interest on a principal amount at a fixed rate for a chosen number of "
         "years, including the total balance and the monthly interest equivalent.",
    h1="Simple interest calculator",
    lede="Work out simple interest — interest paid only on the original principal — plus the total "
         "amount and the equivalent monthly interest.",
    fields=[num("principal", "Principal", 10000, unit=MONEY, pre="$", mn=1, mx=100000000, step=500),
            num("rate", "Annual interest rate", 5, unit="%", mn=0, mx=100, step="0.01"),
            num("years", "Time", 3, unit="years", mn=0, mx=100, step=0.25)],
    outs=[("interest", "Interest earned", "money"),
          ("total", "Total (principal + interest)", "money"),
          ("monthly", "Interest per month", "money")],
    js="""
var P=v.principal,r=v.rate/100,y=v.years;
return {interest:P*r*y,total:P*(1+r*y),monthly:P*r/12};
""",
    py=_simple_py,
    how="""<p>Simple interest is the most straightforward interest calculation: each year you earn the
same percentage of the original principal, and the interest itself never earns interest. Lending
$10,000 at 5% simple interest for three years produces $500 a year, $1,500 in total, and a final
balance of $11,500.</p>
<p>That is genuinely how many short-term loans, some bonds and peer-to-peer arrangements work. It is
not how bank accounts, mortgages or credit cards work — those compound, meaning interest is added
to the balance and starts earning interest itself. When comparing a simple-interest offer with a
compounding one, convert both to an annual effective rate first, or the comparison will mislead.</p>""",
    formula="""<p>For principal <em>P</em>, annual rate <em>r</em> (decimal) and time <em>t</em>
(years):</p>
<div class="fml"><code>interest = P · r · t
total    = P · (1 + r · t)
monthly  = P · r / 12</code></div>
<p>The formula is linear in time: doubling the term doubles the interest. Compounding, by
contrast, grows exponentially.</p>""",
    example="Simple interest on {principal} at {rate}% for {years} years is {interest}. The total "
            "balance is {total}, and the interest works out to {monthly} a month while the principal "
            "stays unchanged.",
    mistakes=[
        "<strong>Using simple interest for a mortgage.</strong> Mortgages, cards and most loans "
        "compound monthly. Simple interest understates the true cost over long periods.",
        "<strong>Mixing up rates and time.</strong> The formula needs the rate as a decimal and the "
        "time in years. A six-month term is 0.5 years, not 6.",
        "<strong>Ignoring the compounding alternative.</strong> At 5% for 30 years, compound "
        "interest produces roughly 4.3× the simple-interest amount on the same principal.",
    ],
    faq=[
        ("Where is simple interest used?",
         "Common uses include some car loans advertised on simple-interest terms, short-term "
         "personal loans, certain bonds and promissory notes, and simple interest savings "
         "arrangements between individuals."),
        ("What is the difference between simple and compound interest?",
         "Simple interest is always calculated on the original principal. Compound interest is "
         "calculated on the principal plus previously earned interest, so it grows faster the longer "
         "it runs."),
        ("How do I convert simple interest to an annual effective rate?",
         "If the simple interest is paid once at maturity, the effective annual rate is higher than "
         "the nominal rate for terms under a year, and the same or lower for longer terms. Use the "
         "compound interest calculator to compare precisely."),
    ],
    related=["compound-interest", "apy-vs-apr", "loan-payment", "roi-calculator"],
    note="Interest is not compounded and no fees or taxes are included.",
)


CALCS = [COMPOUND, SAVINGS_GOAL, RETIREMENT, K401, INFLATION, ROI, CAGR, APY, SIMPLE]
