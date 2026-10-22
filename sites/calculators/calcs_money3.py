#!/usr/bin/env python3
"""Third wave of money calculators: net worth, stock profit, crypto profit, emergency fund.

Every calculator has a Python implementation (server-rendered initial result) and a JavaScript twin
(live result) that must agree; see core.py for the field/output contract.
"""
import math

from core import calc, num, sel

MONEY = "USD"


NET_WORTH = calc(
    slug="net-worth-calculator", name="Net Worth Calculator", cat="investing",
    title="Net Worth Calculator — Add Up Assets and Liabilities",
    desc="Work out your net worth from cash, investments, property and other assets minus every "
         "debt, and see how concentrated your balance sheet is.",
    h1="Net worth calculator",
    lede="Net worth is everything you own minus everything you owe. Enter your balances to see the "
         "total, and what share of your assets are liquid.",
    fields=[num("cash", "Cash and savings", 25000, unit=MONEY, mn=0, mx=10**9),
            num("investments", "Investments and retirement accounts", 150000, unit=MONEY, mn=0, mx=10**9),
            num("property", "Property and other assets", 300000, unit=MONEY, mn=0, mx=10**9),
            num("debts", "Total debts (mortgage, loans, cards)", 220000, unit=MONEY, mn=0, mx=10**9)],
    outs=[("assets", "Total assets", "money0"), ("debts", "Total debts", "money0"),
          ("net", "Net worth", "money0"), ("liquid", "Liquid share of assets", "pct1")],
    js="""
var a=v.cash+v.investments+v.property, d=v.debts, net=a-d;
return { assets: a, debts: d, net: net, liquid: a>0 ? v.cash/a*100 : 0 };
""",
    py=lambda v: {
        "assets": float(v["cash"]) + float(v["investments"]) + float(v["property"]),
        "debts": float(v["debts"]),
        "net": (float(v["cash"]) + float(v["investments"]) + float(v["property"]) - float(v["debts"])),
        "liquid": ((float(v["cash"]) / (float(v["cash"]) + float(v["investments"]) + float(v["property"])) * 100)
                   if (float(v["cash"]) + float(v["investments"]) + float(v["property"])) > 0 else 0),
    },
    how="""<p>Net worth is a stock, not a flow: it is a snapshot of balances at one moment. Income and
spending change it over time, but only through what they do to assets and debts.</p>
<p>A high net worth built almost entirely from one house is fragile: the asset is illiquid and its
price is local. The liquid share shown here (cash divided by total assets) is a rough measure of
how much of your balance sheet you could actually spend without selling property.</p>""",
    formula="""<div class="fml"><code>total assets = cash + investments + property + other assets
net worth = total assets − total debts
liquid share = cash ÷ total assets × 100</code></div>
<p>With $25,000 cash, $150,000 invested, $300,000 of property and $220,000 of debt, net worth is
$255,000 and only 5.3% of assets are liquid.</p>""",
    example="Your assets total {assets}, debts are {debts}, so net worth is {net}. Cash is {liquid} of "
            "total assets.",
    mistakes=["<strong>Counting a car or furniture at purchase price.</strong> These depreciate fast; "
              "use a realistic resale value, or leave them out.",
              "<strong>Forgetting the mortgage balance.</strong> The house is an asset and the loan is a "
              "liability — include both or the number is meaningless.",
              "<strong>Comparing net worth across ages.</strong> Early-career net worth is often near "
              "zero or negative while student loans are being repaid; the trend matters more than the level."],
    faq=[("Is net worth the same as savings?",
          "No. Savings are one asset. Net worth nets every asset against every debt, including a "
          "mortgage and retirement accounts."),
         ("Should retirement accounts be included?",
          "Yes, at their current balance. They are assets, even though they are not accessible without "
          "penalty before retirement age — which is why the liquid share is shown separately."),
         ("How often should I calculate it?",
          "Quarterly is enough for most people; monthly if you are tracking a payoff plan closely.")],
    related=["savings-goal", "emergency-fund-calculator", "compound-interest"],
    note="A snapshot of balances you enter; not a valuation of your finances or an investment recommendation.",
)


STOCK_PROFIT = calc(
    slug="stock-profit-calculator", name="Stock Profit Calculator", cat="investing",
    title="Stock Profit Calculator — Profit, Loss and Return After Fees",
    desc="Calculate the profit or loss on a stock trade from shares, buy price, sell price and "
         "commission, with the percentage return on cost.",
    h1="Stock profit calculator",
    lede="Enter the number of shares, the price you paid, the price you sold at and the commission to "
         "see the profit, the total cost and the percentage return.",
    fields=[num("shares", "Number of shares", 100, unit="shares", mn=1, mx=10**7),
            num("buy", "Buy price per share", 50, unit=MONEY, mn=0, mx=10**7, step="0.01"),
            num("sell", "Sell price per share", 62, unit=MONEY, mn=0, mx=10**7, step="0.01"),
            num("fee", "Commission per trade", 5, unit=MONEY, mn=0, mx=10**6, step="0.01")],
    outs=[("cost", "Total cost", "money0"), ("proceeds", "Net proceeds", "money0"),
          ("profit", "Profit / loss", "money0"), ("pct", "Return on cost", "pct1")],
    js="""
var cost=v.shares*v.buy+v.fee, proceeds=v.shares*v.sell-v.fee;
var profit=proceeds-cost;
return { cost: cost, proceeds: proceeds, profit: profit, pct: cost>0 ? profit/cost*100 : 0 };
""",
    py=lambda v: {
        "cost": float(v["shares"]) * float(v["buy"]) + float(v["fee"]),
        "proceeds": float(v["shares"]) * float(v["sell"]) - float(v["fee"]),
        "profit": (float(v["shares"]) * float(v["sell"]) - float(v["fee"])
                   - float(v["shares"]) * float(v["buy"]) - float(v["fee"])),
        "pct": (((float(v["shares"]) * float(v["sell"]) - float(v["fee"])
                  - float(v["shares"]) * float(v["buy"]) - float(v["fee"]))
                 / (float(v["shares"]) * float(v["buy"]) + float(v["fee"])) * 100)
                if (float(v["shares"]) * float(v["buy"]) + float(v["fee"])) > 0 else 0),
    },
    how="""<p>The cost of a trade is not just price times shares: commission (and any regulatory fees)
are charged on both sides, so they reduce the profit twice. The return on cost divides the profit by
what you actually put in, which is the number to compare with an index fund or a savings rate.</p>
<p>This calculator covers long trades: buy first, sell later. For a short sale the order is reversed
and the loss can exceed the initial cost.</p>""",
    formula="""<div class="fml"><code>total cost = shares × buy price + commission
net proceeds = shares × sell price − commission
profit = net proceeds − total cost
return on cost = profit ÷ total cost × 100</code></div>
<p>100 shares bought at $50 and sold at $62 with $5 commission per trade: cost $5,005, proceeds
$6,195, profit $1,190 — a 23.8% return.</p>""",
    example="The trade cost {cost} and returned {proceeds}, so the profit is {profit} — {pct} on cost.",
    mistakes=["<strong>Ignoring taxes.</strong> Short-term gains are taxed as ordinary income in the US; "
              "the after-tax return can be several points lower.",
              "<strong>Comparing to price change only.</strong> A 24% price rise with two commissions is "
              "not a 24% return — the calculator shows the real figure.",
              "<strong>Forgetting currency and platform fees.</strong> Add them to the commission field "
              "so the return reflects everything you paid."],
    faq=[("Does the calculator handle short selling?",
          "No. It assumes you buy at the buy price and sell at the sell price. For a short sale, swap "
          "the prices and note that the loss is not capped."),
         ("Are dividends included?",
          "No — only the capital gain or loss between the two prices. Add dividends you received to "
          "the profit if you want the total return."),
         ("What counts as commission?",
          "Any fee charged to execute the trade, including platform fees and regulatory charges.")],
    related=["roi-calculator", "dividend-income-calculator", "compound-interest"],
    note="Before tax and any account-level fees you did not enter. Not investment advice.",
)


CRYPTO_PROFIT = calc(
    slug="crypto-profit-calculator", name="Crypto Profit Calculator", cat="investing",
    title="Crypto Profit Calculator — Profit and Return After Fees",
    desc="Work out the gain on a crypto trade from the amount invested, buy and sell prices and the "
         "exchange fee charged on each side.",
    h1="Crypto profit calculator",
    lede="Enter what you invested, the price you bought at, the price you sold at and the exchange "
         "fee to see your profit, the coins bought and the return after fees.",
    fields=[num("invest", "Amount invested", 5000, unit=MONEY, mn=1, mx=10**9),
            num("buy", "Buy price per coin", 30000, unit=MONEY, mn=0.000001, mx=10**9, step="0.000001"),
            num("sell", "Sell price per coin", 45000, unit=MONEY, mn=0.000001, mx=10**9, step="0.000001"),
            num("fee", "Exchange fee per side", 0.5, unit="%", mn=0, mx=10, step="0.01")],
    outs=[("coins", "Coins bought", "num"), ("proceeds", "Proceeds after fees", "money"),
          ("profit", "Profit / loss", "money"), ("pct", "Return after fees", "pct1")],
    js="""
var fee=v.fee/100;
var investNet=v.invest*(1-fee);
var coins=investNet/v.buy;
var proceeds=coins*v.sell*(1-fee);
var profit=proceeds-v.invest;
return { coins: coins, proceeds: proceeds, profit: profit, pct: v.invest>0 ? profit/v.invest*100 : 0 };
""",
    py=lambda v: {
        "coins": (float(v["invest"]) * (1 - float(v["fee"]) / 100) / float(v["buy"]))
                 if float(v["buy"]) > 0 else 0,
        "proceeds": (float(v["invest"]) * (1 - float(v["fee"]) / 100) / float(v["buy"])
                     * float(v["sell"]) * (1 - float(v["fee"]) / 100)) if float(v["buy"]) > 0 else 0,
        "profit": ((float(v["invest"]) * (1 - float(v["fee"]) / 100) / float(v["buy"])
                    * float(v["sell"]) * (1 - float(v["fee"]) / 100)) - float(v["invest"]))
                  if float(v["buy"]) > 0 else 0,
        "pct": (((float(v["invest"]) * (1 - float(v["fee"]) / 100) / float(v["buy"])
                  * float(v["sell"]) * (1 - float(v["fee"]) / 100)) - float(v["invest"]))
                / float(v["invest"]) * 100) if float(v["invest"]) > 0 and float(v["buy"]) > 0 else 0,
    },
    how="""<p>Crypto exchanges charge a fee on each side of a trade, so fees compound against you: a
0.5% buy fee and a 0.5% sell fee cost about 1% of the position, and that is before spreads. The
calculator applies the fee at both ends, then works out how many coins your net invest bought.</p>
<p>The percentage shown is the return on the amount you put in, after fees and before tax. In many
countries every disposal is a taxable event, so a profitable trade may still leave you with a tax
bill if you re-buy at a higher price later.</p>""",
    formula="""<div class="fml"><code>coins bought = (amount invested × (1 − fee)) ÷ buy price
proceeds = coins × sell price × (1 − fee)
profit = proceeds − amount invested
return = profit ÷ amount invested × 100</code></div>
<p>$5,000 invested at $30,000 with a 0.5% fee: 0.16583 coins. Selling at $45,000 after another 0.5%
fee gives $7,428.75 — a profit of $2,428.75, or 48.6%.</p>""",
    example="You bought {coins} coins. After fees the sale proceeds are {proceeds}, so the profit is "
            "{profit}, or {pct} on the amount invested.",
    mistakes=["<strong>Ignoring the fee on entry.</strong> The fee reduces the coins you actually own, "
              "not just the cash you receive when you sell.",
              "<strong>Forgetting the tax event.</strong> Selling at a profit is usually taxable even "
              "if you immediately reinvest.",
              "<strong>Assuming one sell price.</strong> Large orders can move the market; slippage "
              "makes the realised price worse than the quoted one."],
    faq=[("Does it handle multiple buys?",
          "No — it treats the position as a single purchase. For several buys, calculate each lot "
          "separately and add the results."),
         ("What fee should I enter?",
          "The exchange's trading fee per side, as a percentage. Add the spread to it if you are "
          "filling market orders."),
         ("Are staking rewards included?",
          "No. Add the value of rewards you received to the proceeds if you want the total return.")],
    related=["stock-profit-calculator", "roi-calculator", "compound-interest"],
    note="Before income or capital-gains tax. Prices are volatile; the result is a planning estimate.",
)


EMERGENCY_FUND = calc(
    slug="emergency-fund-calculator", name="Emergency Fund Calculator", cat="investing",
    title="Emergency Fund Calculator — How Much You Need and How Long to Save It",
    desc="Work out the size of an emergency fund from your monthly essential spending and months of "
         "cover, the gap to your current savings, and how long it takes to close it.",
    h1="Emergency fund calculator",
    lede="An emergency fund is months of essential spending in cash. Enter your expenses, your target "
         "and what you already have to see the gap and how long it takes to fill it.",
    fields=[num("expenses", "Monthly essential expenses", 3200, unit=MONEY, mn=0, mx=10**7),
            num("months", "Months of cover", 6, unit="months", mn=1, mx=36),
            num("saved", "Already saved for emergencies", 4000, unit=MONEY, mn=0, mx=10**7),
            num("monthly", "Monthly amount you can set aside", 400, unit=MONEY, mn=0, mx=10**6)],
    outs=[("target", "Target emergency fund", "money0"), ("gap", "Gap to target", "money0"),
          ("monthsTo", "Months to reach the target", "months"), ("monthly12", "Monthly needed to finish in 12 months", "money0")],
    js="""
var target=v.expenses*v.months, gap=Math.max(0,target-v.saved);
var monthsTo = gap<=0 ? 0 : (v.monthly>0 ? Math.ceil(gap/v.monthly) : null);
var monthly12 = gap<=0 ? 0 : gap/12;
return { target: target, gap: gap, monthsTo: monthsTo, monthly12: monthly12 };
""",
    py=lambda v: {
        "target": float(v["expenses"]) * float(v["months"]),
        "gap": max(0.0, float(v["expenses"]) * float(v["months"]) - float(v["saved"])),
        "monthsTo": (0 if float(v["expenses"]) * float(v["months"]) <= float(v["saved"])
                     else (math.ceil((float(v["expenses"]) * float(v["months"]) - float(v["saved"])) / float(v["monthly"]))
                           if float(v["monthly"]) > 0 else None)),
        "monthly12": (max(0.0, float(v["expenses"]) * float(v["months"]) - float(v["saved"])) / 12),
    },
    how="""<p>An emergency fund covers the gap between losing income and finding income again: job loss,
a medical bill, a car that fails inspection. It is held in cash or a high-yield savings account, not
invested, because the point is certainty rather than return.</p>
<p>The usual guidance is three to six months of <em>essential</em> spending — rent, food, utilities,
insurance and debt minimums — not your full salary. Two incomes in a stable industry need less; a
single income, commission-based pay or dependants argue for more.</p>""",
    formula="""<div class="fml"><code>target = monthly essential expenses × months of cover
gap = max(0, target − already saved)
months to reach it = gap ÷ monthly saving</code></div>
<p>$3,200 of essentials with six months of cover needs $19,200. With $4,000 saved the gap is $15,200;
saving $400 a month closes it in 38 months, or $1,267 a month gets there in a year.</p>""",
    example="Six months of cover needs {target}. You have already saved part of it, so the gap is "
            "{gap}. At your monthly rate it takes {monthsTo}; finishing in 12 months needs {monthly12} a month.",
    mistakes=["<strong>Investing the fund.</strong> Markets can fall exactly when you lose your job; "
              "keep emergencies in cash.",
              "<strong>Basing it on income, not spending.</strong> Cover is about expenses you cannot "
              "cut, not what you earn.",
              "<strong>Stopping at the first months.</strong> A one-month buffer handles small shocks; "
              "three to six months is what absorbs a job loss."],
    faq=[("Where should the money sit?",
          "A separate high-yield savings account: fast to reach, insured (FDIC/NCUA or equivalent) and "
          "not mixed with everyday spending."),
         ("Should I pay off debt first?",
          "Compare the interest rate on the debt with the comfort of a buffer. High-interest credit "
          "cards usually win; keep a small starter fund while paying them down."),
         ("Does the calculator include income tax?",
          "No. Use expenses net of tax, and remember a job loss may also change tax and benefit "
          "positions.")],
    related=["savings-goal", "net-worth-calculator", "budget-calculator"],
    note="Planning estimate. Emergency-fund size depends on income stability, dependants and insurance.",
)


CALCS = [NET_WORTH, STOCK_PROFIT, CRYPTO_PROFIT, EMERGENCY_FUND]
