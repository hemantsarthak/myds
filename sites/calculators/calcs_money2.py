#!/usr/bin/env python3
"""Second wave of money calculators: retirement withdrawal, debt payoff, biweekly mortgage,
commission, plus a sleep-cycle planner.

Every calculator has a Python implementation (server-rendered initial result) and a JavaScript twin
(live result) that must agree; see core.py for the field/output contract.
"""
from core import calc, num, sel, tim, fnum, r0

MONEY = "USD"


def _pmt(principal, annual_rate, months):
    """Fixed monthly payment for a fully amortising loan."""
    if principal <= 0 or months <= 0:
        return 0.0
    r = annual_rate / 100.0 / 12.0
    if r == 0:
        return principal / months
    return principal * r / (1 - (1 + r) ** -months)


def _payoff(balance, apr, payment):
    """Months to clear a balance at a fixed payment, plus total interest."""
    r = apr / 100.0 / 12.0
    if balance <= 0:
        return 0, 0.0, 0.0
    if payment <= balance * r:
        return None, None, None  # payment never reduces the balance
    months, interest = 0, 0.0
    b = balance
    while b > 0.005 and months < 1200:
        i = b * r
        interest += i
        b = b + i - payment
        months += 1
    return months, interest, balance + interest


RETIREMENT_WITHDRAWAL = calc(
    slug="retirement-withdrawal-calculator", name="Retirement Withdrawal Calculator", cat="investing",
    title="Retirement Withdrawal Calculator — The 4% Rule and Safe Withdrawal Rates",
    desc="Work out how much you can withdraw from a retirement portfolio each year at a given "
         "withdrawal rate, and how the balance changes over a 30-year retirement.",
    h1="Retirement withdrawal calculator",
    lede="Enter a portfolio balance and a withdrawal rate to see the annual and monthly income it "
         "supports, and what the balance looks like after 30 years at a given return.",
    fields=[num("balance", "Portfolio balance", 1000000, unit=MONEY, mn=0, mx=10**9),
            num("rate", "Withdrawal rate", 4, unit="%", mn=0.1, mx=20, step="0.1"),
            num("growth", "Expected return after inflation", 4, unit="%", mn=-5, mx=15, step="0.1"),
            num("years", "Years in retirement", 30, unit="years", mn=1, mx=60)],
    outs=[("annual", "Annual withdrawal", "money"), ("monthly", "Monthly withdrawal", "money"),
          ("ending", "Balance after the period", "money"), ("safe", "At 3.5% instead", "money")],
    js="""
var bal=v.balance, wr=v.rate/100, g=v.growth/100, n=Math.round(v.years);
var annual=bal*wr, monthly=annual/12, b=bal;
for(var i=0;i<n;i++){ b=b*(1+g)-annual; if(b<0){b=0;break;} }
return { annual: annual, monthly: monthly, ending: b, safe: bal*0.035 };
""",
    py=lambda v: {
        "annual": float(v["balance"]) * float(v["rate"]) / 100,
        "monthly": float(v["balance"]) * float(v["rate"]) / 100 / 12,
        "ending": _ending_balance(float(v["balance"]), float(v["growth"]) / 100,
                                  float(v["balance"]) * float(v["rate"]) / 100, int(v["years"])),
        "safe": float(v["balance"]) * 0.035,
    },
    how="""<p>The withdrawal rate is the share of the portfolio you take out each year. The famous
"4% rule" comes from the Trinity study: withdrawing 4% of the starting balance, adjusted for
inflation, historically lasted at least 30 years in most US market periods. Lower rates are safer;
3–3.5% is common for retirements longer than 30 years or for conservative portfolios.</p>
<p>The calculator also grows the balance at an expected real (after-inflation) return and subtracts
the withdrawal each year, so you can see whether the portfolio survives the period.</p>""",
    formula="""<div class="fml"><code>annual withdrawal = balance × withdrawal rate
monthly withdrawal = annual withdrawal ÷ 12
next-year balance = balance × (1 + real return) − annual withdrawal</code></div>
<p>With $1,000,000 at a 4% rate, the first year pays $40,000 — about $3,333 a month.</p>""",
    example="A {balance} portfolio at a {rate}% withdrawal rate pays {annual} a year, or {monthly} a "
            "month. At a {growth}% real return over {years} years the balance would be {ending}.",
    mistakes=["<strong>Ignoring sequence-of-returns risk.</strong> A bad market in the first years of "
              "retirement hurts far more than the same decline later, because withdrawals lock in losses.",
              "<strong>Forgetting fees and taxes.</strong> Fund fees and income tax reduce the real "
              "return; a 4% withdrawal with 1.5% of costs is closer to 2.5% net.",
              "<strong>Assuming a constant return.</strong> Real markets are volatile; model a range of "
              "returns rather than one number."],
    faq=[("Is the 4% rule still safe?",
          "It remains a useful planning anchor for a 30-year retirement, but many planners now suggest "
          "3.5% or less for longer retirements or higher-cost portfolios."),
         ("Should I adjust withdrawals for inflation?",
          "Yes — the classic rule increases the withdrawal each year with inflation. If markets fall "
          "sharply, cutting withdrawals temporarily helps the portfolio survive."),
         ("What return should I assume?",
          "Use a real (after-inflation) return, typically 3–5% for a balanced portfolio. The calculator "
          "compounds whatever rate you enter.")],
    related=["savings-goal", "compound-interest", "inflation-calculator"],
    note="Planning estimate, not financial advice. Returns and withdrawal rates are assumptions.",
)


def _ending_balance(balance, growth, annual, years):
    b = balance
    for _ in range(max(0, int(years))):
        b = b * (1 + growth) - annual
        if b < 0:
            return 0.0
    return b


DEBT_PAYOFF = calc(
    slug="debt-payoff-calculator", name="Debt Payoff Calculator", cat="loans",
    title="Debt Payoff Calculator — Months to Clear a Balance and Total Interest",
    desc="Enter a balance, APR and monthly payment to see how many months it takes to pay off the "
         "debt, how much interest you pay, and how a bigger payment changes the result.",
    h1="Debt payoff calculator",
    lede="See how long a balance takes to clear at a fixed monthly payment, and how much a larger "
         "payment saves in interest.",
    fields=[num("balance", "Balance owed", 5000, unit=MONEY, mn=1, mx=10**8),
            num("apr", "Annual interest rate (APR)", 22, unit="%", mn=0, mx=60, step="0.1"),
            num("payment", "Monthly payment", 250, unit=MONEY, mn=1, mx=10**6)],
    outs=[("months", "Months to pay off", "text"), ("interest", "Total interest", "money"),
          ("total", "Total paid", "money"), ("extra", "Pay 25% more — months", "text")],
    js="""
function sim(bal, apr, pay){
  var r=apr/100/12, m=0, i=0;
  if(pay<=bal*r) return null;
  while(bal>0.005 && m<1200){ var ii=bal*r; i+=ii; bal=bal+ii-pay; m++; }
  return [m,i];
}
var a=sim(v.balance, v.apr, v.payment), b=sim(v.balance, v.apr, v.payment*1.25);
return { months: a? a[0]+' months':'never', interest: a?a[1]:0, total: a? v.balance+a[1]:0,
         extra: b? b[0]+' months':'never' };
""",
    py=lambda v: _debt_result(v),
    how="""<p>Each month the lender charges interest on the outstanding balance, then your payment
reduces the balance by the rest. The lower the payment relative to the interest charge, the longer
the payoff — and if the payment is smaller than the monthly interest, the balance never falls.</p>
<p>The calculator also shows what happens if you pay 25% more each month, which is usually the
fastest way to cut both the term and the total interest.</p>""",
    formula="""<div class="fml"><code>monthly interest = balance × APR ÷ 12
new balance = balance + monthly interest − payment</code></div>
<p>Repeat until the balance reaches zero; the months counted and the interest accumulated are the "
results.</p>""",
    example="A {balance} balance at {apr}% APR with a {payment} monthly payment takes {months} to "
            "clear and costs {interest} in interest; paying 25% more would take {extra}.",
    mistakes=["<strong>Paying only the minimum.</strong> Minimum payments on high-APR cards are often "
              "barely above the monthly interest, stretching payoff to decades.",
              "<strong>Ignoring new spending.</strong> A payoff plan only works if you stop adding new "
              "charges to the balance.",
              "<strong>Not checking the APR.</strong> The rate matters more than the balance: 29% APR "
              "turns a small balance into a long, expensive one."],
    faq=[("Why does my balance never go down?",
          "If the monthly payment is less than the monthly interest charge, the balance grows. The "
          "calculator shows 'never' when that happens."),
         ("Should I pay off the highest rate first?",
          "Mathematically yes — the avalanche method (highest APR first) minimises interest. The "
          "snowball method (smallest balance first) is better for motivation."),
         ("Does paying extra reduce interest?",
          "Yes, every extra dollar goes straight to principal and removes all future interest that "
          "principal would have generated.")],
    related=["credit-card-payoff", "loan-payment", "compound-interest"],
    note="Assumes a fixed APR and no new charges.",
)


def _debt_result(v):
    months, interest, total = _payoff(float(v["balance"]), float(v["apr"]), float(v["payment"]))
    m2, _i2, _t2 = _payoff(float(v["balance"]), float(v["apr"]), float(v["payment"]) * 1.25)
    return {
        "months": f"{months} months" if months else "never",
        "interest": interest or 0.0,
        "total": total or 0.0,
        "extra": f"{m2} months" if m2 else "never",
    }


BIWEEKLY_MORTGAGE = calc(
    slug="biweekly-mortgage-calculator", name="Biweekly Mortgage Calculator", cat="loans",
    title="Biweekly Mortgage Calculator — Interest and Years Saved",
    desc="Compare a monthly mortgage with biweekly payments: how much interest you save, how many "
         "years come off the term, and what the extra payment effectively does.",
    h1="Biweekly mortgage calculator",
    lede="Paying half the monthly payment every two weeks means 26 half-payments a year — one extra "
         "monthly payment. See what that saves.",
    fields=[num("amount", "Loan amount", 300000, unit=MONEY, mn=1000, mx=10**8),
            num("rate", "Interest rate", 6.5, unit="%", mn=0.1, mx=20, step="0.1"),
            num("years", "Loan term", 30, unit="years", mn=1, mx=40)],
    outs=[("monthly", "Monthly payment", "money"), ("biweekly", "Biweekly payment", "money"),
          ("interest_saved", "Interest saved", "money"), ("years_saved", "Years saved", "text")],
    js="""
function pmt(p,rp,n){ rp=rp/100/12; return rp? p*rp/(1-Math.pow(1+rp,-n)) : p/n; }
var p=v.amount, r=v.rate, n=Math.round(v.years*12);
var m=pmt(p,r,n), totalM=m*n, interestM=totalM-p;
// biweekly: pay m/2 every 2 weeks => m*26/12 per month equivalent
var eff=m*13/12, b=p, i=0, months=0, rb=r/100/12;
while(b>0.01 && months<1200){ var ii=b*rb; i+=ii; b=b+ii-eff; months++; }
return { monthly:m, biweekly:m/2, interest_saved: interestM-i,
         years_saved: ((n-months)/12).toFixed(1)+' years' };
""",
    py=lambda v: _biweekly_result(v),
    how="""<p>A standard mortgage has 12 monthly payments a year. Paying half the monthly amount every
two weeks gives 26 half-payments — 13 full payments — so you make one extra payment a year, and
each extra payment goes entirely to principal. The effect compounds: most 30-year mortgages finish
about 4–6 years early.</p>
<p>You do not have to use a biweekly programme: making one extra monthly payment a year, or adding
1/12 of your payment to each month, has nearly the same effect without the fees some lenders charge
for biweekly setups.</p>""",
    formula="""<div class="fml"><code>monthly payment = P × r ÷ (1 − (1 + r)^−n)
biweekly payment = monthly payment ÷ 2
effective monthly payment = biweekly × 26 ÷ 12</code></div>""",
    example="On a {amount} loan at {rate}% for {years} years, the monthly payment is {monthly} and "
            "the biweekly payment is {biweekly}. Biweekly payments save {interest_saved} in interest "
            "and cut {years_saved} off the term.",
    mistakes=["<strong>Paying a setup fee.</strong> Third-party biweekly services charge for something "
              "you can do yourself by adding 1/12 to each monthly payment.",
              "<strong>Letting the lender hold the half-payments.</strong> Some plans debit every two "
              "weeks but only apply the payment monthly, which reduces the benefit.",
              "<strong>Forgetting the emergency fund.</strong> Extra principal payments are hard to "
              "reverse; keep cash reserves first."],
    faq=[("Does biweekly really save that much?",
          "It saves the interest on one extra monthly payment a year, compounded — typically 4–6 "
          "years and tens of thousands of dollars on a 30-year mortgage."),
         ("Is biweekly better than a shorter term?",
          "A 15-year loan usually saves more interest but raises the required payment; biweekly is "
          "optional extra principal, so it is more flexible."),
         ("Can I just pay extra each month instead?",
          "Yes — adding 1/12 of the payment monthly is equivalent and avoids programme fees.")],
    related=["mortgage-payment", "mortgage-amortization", "loan-payment"],
    note="Assumes the extra payment is applied to principal immediately.",
)


def _biweekly_result(v):
    p, rate, years = float(v["amount"]), float(v["rate"]), int(v["years"])
    n = years * 12
    m = _pmt(p, rate, n)
    total_interest_monthly = m * n - p
    eff = m * 13 / 12
    r = rate / 100 / 12
    b, interest, months = p, 0.0, 0
    while b > 0.01 and months < 1200:
        i = b * r
        interest += i
        b = b + i - eff
        months += 1
    return {
        "monthly": m, "biweekly": m / 2,
        "interest_saved": max(0.0, total_interest_monthly - interest),
        "years_saved": f"{(n - months) / 12:.1f} years",
    }


COMMISSION = calc(
    slug="commission-calculator", name="Commission Calculator", cat="salary",
    title="Commission Calculator — Sales Commission and Split Payout",
    desc="Calculate the commission on a sale at a given rate, and what you keep after a broker or "
         "team split.",
    h1="Commission calculator",
    lede="Enter the sale price and commission rate to see the gross commission, then apply a split "
    "to see your payout.",
    fields=[num("price", "Sale price", 250000, unit=MONEY, mn=0, mx=10**9),
            num("rate", "Commission rate", 3, unit="%", mn=0, mx=100, step="0.1"),
            num("split", "Your split", 70, unit="%", mn=0, mx=100)],
    outs=[("commission", "Gross commission", "money"), ("payout", "Your payout", "money"),
          ("broker", "Broker/team share", "money"), ("per_side", "If split 50/50 with another agent", "money")],
    js="""
var c=v.price*v.rate/100, pay=c*v.split/100;
return { commission:c, payout:pay, broker:c-pay, per_side:pay/2 };
""",
    py=lambda v: {
        "commission": float(v["price"]) * float(v["rate"]) / 100,
        "payout": float(v["price"]) * float(v["rate"]) / 100 * float(v["split"]) / 100,
        "broker": float(v["price"]) * float(v["rate"]) / 100 * (1 - float(v["split"]) / 100),
        "per_side": float(v["price"]) * float(v["rate"]) / 100 * float(v["split"]) / 100 / 2,
    },
    how="""<p>Commission is a percentage of the sale price. In real estate the listing broker and the
buyer's broker typically split the total commission, and each broker then splits with their agent —
so a 3% commission on a $250,000 sale can end up as a very different number in the agent's pocket.</p>
<p>Use the split field to model your agreement: 70/30 is common for newer agents, 100% for agents who
pay desk fees instead. The last output shows the agent's share if two agents split the same side.</p>""",
    formula="""<div class="fml"><code>gross commission = sale price × commission rate
your payout = gross commission × your split
broker share = gross commission − your payout</code></div>""",
    example="A {price} sale at a {rate}% commission pays {commission} gross; with a {split}% split "
            "you keep {payout} and the broker keeps {broker}.",
    mistakes=["<strong>Forgetting the other side.</strong> The quoted rate often covers both agents; "
              "each side takes half before your own split.",
              "<strong>Ignoring transaction fees.</strong> E&O insurance, desk fees and marketing costs "
              "come out of your payout, not the gross commission.",
              "<strong>Assuming commission is guaranteed.</strong> Commissions are negotiable and can "
              "change with the deal structure."],
    faq=[("How is commission calculated?",
          "Sale price multiplied by the commission rate. On a $250,000 sale at 3% the gross commission "
          "is $7,500."),
         ("What is a commission split?",
          "The share of the gross commission you keep under your brokerage agreement — commonly 70/30 "
          "for newer agents and 80/20 or higher for experienced ones."),
         ("Do both agents get the full rate?",
          "Usually the total commission is split between the two sides of the deal, then each agent "
          "splits their side with their broker.")],
    related=["hourly-to-salary", "salary-to-hourly", "raise-calculator"],
    note="Simplified model; actual agreements vary.",
)


SLEEP_CYCLE = calc(
    slug="sleep-cycle-calculator", name="Sleep Cycle Calculator", cat="health",
    title="Sleep Cycle Calculator — Best Bedtimes for a Wake-Up Time",
    desc="Work backwards from a wake-up time through 90-minute sleep cycles to find bedtimes that "
         "let you wake between cycles, plus a fall-asleep buffer.",
    h1="Sleep cycle calculator",
    lede="Sleep runs in roughly 90-minute cycles. Work backwards from your wake-up time to find "
         "bedtimes that land between cycles.",
    fields=[tim("wake", "Wake-up time", "07:00"),
            num("cycles", "Sleep cycles to plan", 5, unit="cycles", mn=3, mx=6),
            num("buffer", "Minutes to fall asleep", 15, unit="min", mn=0, mx=60)],
    outs=[("bedtime", "Bedtime (last cycle)", "text"), ("alt1", "Alternate bedtime", "text"),
          ("alt2", "Second alternate", "text"), ("hours", "Time asleep", "text")],
    js="""
function mins(t){ var p=t.split(':'); return (+p[0])*60+(+p[1]); }
function fmt(m){ m=((m%1440)+1440)%1440; var h=Math.floor(m/60), mm=m%60;
  return (h<10?'0':'')+h+':'+(mm<10?'0':'')+mm; }
var w=mins(v.wake), n=Math.round(v.cycles), buf=Math.round(v.buffer);
var b1=w-n*90-buf, b2=b1-90, b3=b1+90;
return { bedtime: fmt(b1), alt1: fmt(b2), alt2: fmt(b3),
         hours: (n*1.5).toFixed(1)+' hours' };
""",
    py=lambda v: _sleep_result(v),
    how="""<p>Sleep cycles last about 90 minutes and end with lighter sleep, which is the easiest moment
to wake. If you wake mid-cycle — especially in deep sleep — you can feel groggy even after a long
night. Working backwards in 90-minute blocks puts the alarm at a cycle boundary.</p>
<p>The calculator subtracts a buffer for the time you take to fall asleep, and shows the bedtimes for
one cycle fewer and one cycle more. Most adults need 5–6 cycles (7.5–9 hours).</p>""",
    formula="""<div class="fml"><code>bedtime = wake-up time − (cycles × 90 minutes) − fall-asleep buffer</code></div>""",
    example="To wake at {wake} after {cycles} cycles (about {hours} of sleep) with a {buffer}-minute "
            "buffer, go to bed at {bedtime}. Alternatives: {alt1} or {alt2}.",
    mistakes=["<strong>Ignoring the fall-asleep buffer.</strong> Most people take 10–20 minutes to fall "
              "asleep; skip it and you cut a cycle short.",
              "<strong>Treating 90 minutes as exact.</strong> Cycle length varies between 70 and 110 "
              "minutes and changes through the night.",
              "<strong>Using it to justify too little sleep.</strong> Four cycles is 6 hours; most "
              "adults need more for sustained performance."],
    faq=[("How long is a sleep cycle?",
          "About 90 minutes on average, ranging roughly 70–110 minutes and lengthening towards "
          "morning."),
         ("How many cycles do I need?",
          "Most adults do best with 5–6 cycles a night, which is 7.5–9 hours including brief "
          "awakenings."),
         ("Why do I feel tired after 8 hours?",
          "Waking in the middle of a deep-sleep cycle can feel worse than waking after fewer cycles "
          "at a light-sleep boundary.")],
    related=["age-calculator", "bmi-calculator", "tdee-calculator"],
    note="Cycle length varies by person; use this as a starting point.",
)


def _sleep_result(v):
    def mins(t):
        h, m = str(t).split(":")[:2]
        return int(h) * 60 + int(m)

    def fmt(m):
        m = ((m % 1440) + 1440) % 1440
        return f"{m // 60:02d}:{m % 60:02d}"

    wake = mins(v["wake"])
    n = int(v["cycles"])
    buf = int(v["buffer"])
    b1 = wake - n * 90 - buf
    return {"bedtime": fmt(b1), "alt1": fmt(b1 - 90), "alt2": fmt(b1 + 90),
            "hours": f"{n * 1.5:.1f} hours"}


CALCS = [RETIREMENT_WITHDRAWAL, DEBT_PAYOFF, BIWEEKLY_MORTGAGE, COMMISSION, SLEEP_CYCLE]
