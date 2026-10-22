#!/usr/bin/env python3
"""Dates & time calculators: age, date difference, countdown, business days,
time duration."""
import datetime as dt
import calendar

from core import calc, num, dat, tim, txt, fnum, r0, iso_add, iso_diff, business_days_between

WEEKDAYS_SUN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def _next_birthday(birth, asof):
    b = dt.date.fromisoformat(str(birth))
    a = dt.date.fromisoformat(str(asof))

    def make(year):
        try:
            return dt.date(year, b.month, b.day)
        except ValueError:
            return dt.date(year, 3, 1) if (b.month, b.day) == (2, 29) else dt.date(year, b.month, b.day)

    nb = make(a.year)
    if nb <= a:
        nb = make(a.year + 1)
    return nb.isoformat()


def _age_ymd(birth, asof):
    b = dt.date.fromisoformat(str(birth))
    a = dt.date.fromisoformat(str(asof))
    y = a.year - b.year
    m = a.month - b.month
    d = a.day - b.day
    if d < 0:
        m -= 1
        pm = a.month - 1
        py = a.year
        if pm < 1:
            pm, py = 12, py - 1
        d += calendar.monthrange(py, pm)[1]
    if m < 0:
        y -= 1
        m += 12
    return y, m, d


def _age_py(v):
    y, m, d = _age_ymd(v["birth"], v["asof"])
    return {"age": f"{y} years, {m} months, {d} days",
            "total_days": iso_diff(v["birth"], v["asof"]),
            "next_birthday": _next_birthday(v["birth"], v["asof"])}


AGE = calc(
    slug="age-calculator", name="Age Calculator", cat="dates",
    title="Age Calculator — Exact Age in Years, Months and Days",
    desc="Calculate your exact age in years, months and days on any date, plus total days lived "
         "and the date of your next birthday.",
    h1="Age calculator",
    lede="Enter a birth date and any reference date to get the exact age in years, months and days, "
         "total days lived and the next birthday.",
    fields=[dat("birth", "Date of birth", "1990-06-15"),
            dat("asof", "Age at date", "today", hint="Defaults to today.")],
    outs=[("age", "Exact age", "text"), ("total_days", "Total days lived", "int"),
          ("next_birthday", "Next birthday", "date")],
    js="""
function ymd(birth, asof) {
  var b=isoToUTC(birth), a=isoToUTC(asof);
  var y=a.getUTCFullYear()-b.getUTCFullYear();
  var m=a.getUTCMonth()-b.getUTCMonth();
  var d=a.getUTCDate()-b.getUTCDate();
  if(d<0){ m-=1; var pm=a.getUTCMonth()-1, py=a.getUTCFullYear();
    if(pm<0){pm=11;py-=1;}
    d+=new Date(Date.UTC(py,pm+1,0)).getUTCDate(); }
  if(m<0){ y-=1; m+=12; }
  return [y,m,d];
}
function nb(birth, asof) {
  var a=isoToUTC(asof), b=isoToUTC(birth);
  var mm=b.getUTCMonth(), dd=b.getUTCDate(), y=a.getUTCFullYear();
  function mk(year){ var d=new Date(Date.UTC(year,mm,dd));
    if(d.getUTCMonth()!==mm) d=new Date(Date.UTC(year,2,1));
    return d; }
  var d=mk(y); if(d<=a) d=mk(y+1);
  return utcToISO(d);
}
var r=ymd(v.birth,v.asof);
return {age:r[0]+' years, '+r[1]+' months, '+r[2]+' days',
        total_days:diffDays(v.birth,v.asof),
        next_birthday:nb(v.birth,v.asof)};
""",
    py=_age_py,
    how="""<p>Exact age is not simply a year count: it is the difference measured from the birth date,
borrowing a month at a time so that the days part stays correct. Someone born on 15 June 1990 is
36 years, 4 months and 7 days old on 22 October 2026 — and 13,278 days old in total, because leap
years add a day roughly every four years.</p>
<p>Total days is the figure you need for medical forms, immigration paperwork and some benefit
calculations. The next-birthday output handles the leap-day edge case: if you were born on 29
February, in non-leap years the birthday is treated as 1 March. Use the reference date field to
answer “how old will I be on that date?” — retirement ages, application deadlines and age limits
are all measured from a specific date, not from today.</p>""",
    formula="""<p>Let the birth date be <em>B</em> and the reference date <em>A</em>. First compute
<em>years = A.year − B.year</em>, then borrow months and days so that each part is non-negative:</p>
<div class="fml"><code>days  = A.day − B.day      (if negative: borrow days in A's previous month)
months = A.month − B.month  (if negative: borrow 12 months)
years = A.year − B.year     (minus 1 if months were borrowed)
total days = (A − B) in days</code></div>
<p>The total-days figure is an exact calendar difference, so it includes every leap day in
between.</p>""",
    example="For a birth date of {birth} measured on {asof}, the exact age is {age}. That is "
            "{total_days} days lived, and the next birthday falls on {next_birthday}.",
    mistakes=[
        "<strong>Subtracting years only.</strong> A naive year difference can be a whole year off "
        "before the birthday has passed.",
        "<strong>Using 365 days per year for total days.</strong> Leap years add an extra day every "
        "four years, which adds up over a lifetime.",
        "<strong>Forgetting time zones.</strong> For age limits, the date that matters is the local "
        "date where the rule applies, not the date on your device."
    ],
    faq=[
        ("How is age calculated exactly?",
         "Full years first, then whole months since the last birthday, then leftover days. The three "
         "parts together describe the elapsed time precisely; total days is the same period counted "
         "as days."),
        ("Why is my age in days different from 365 × years?",
         "Because of leap days and because the months since your last birthday are not a whole "
         "fraction of a year. The exact calendar difference is the number that matters."),
        ("How do you handle a 29 February birthday?",
         "In non-leap years the birthday is treated as 1 March for the purpose of the next-birthday "
         "date. Age in whole years still advances on the normal anniversary logic."),
    ],
    related=["date-difference", "countdown-days", "business-days", "pregnancy-due-date"],
    note="Calendar-date arithmetic; local dates are used, not timestamps.",
)


# ---------------------------------------------------------------------------
def _datediff_py(v):
    days = iso_diff(v["start"], v["end"])
    return {"days": days, "business_days": business_days_between(v["start"], v["end"]),
            "weeks": days / 7, "months": days / 30.436875}


DATE_DIFF = calc(
    slug="date-difference", name="Date Difference Calculator", cat="dates",
    title="Date Difference Calculator — Days, Weeks and Business Days",
    desc="Calculate the number of days, weeks, months and business days between two dates. Useful "
         "for deadlines, project planning and leave calculations.",
    h1="Date difference calculator",
    lede="Pick two dates to get the number of calendar days between them, plus weeks, months and "
         "the count of weekdays.",
    fields=[dat("start", "Start date", "2026-01-01"),
            dat("end", "End date", "today", hint="Defaults to today.")],
    outs=[("days", "Calendar days between", "int"), ("business_days", "Business days (Mon–Fri)", "int"),
          ("weeks", "Weeks", "num1"), ("months", "Months (approx.)", "num1")],
    js="""
var days = diffDays(v.start, v.end);
return {days:days, business_days:bizDays(v.start,v.end), weeks:days/7, months:days/30.436875};
""",
    py=_datediff_py,
    how="""<p>The number of days between two dates is an exact calendar difference: count every day
from the start date forwards to the end date. That means the day after the start date is 1 day
later, and including both endpoints adds one day. This distinction matters for deadlines, contracts
and leave policies, which often specify inclusive counting.</p>
<p>Business days are different from calendar days because weekends are skipped. This calculator
counts weekdays (Monday to Friday) between the dates but does not know about public holidays — if
your project runs through a national holiday, subtract one day for each holiday that falls on a
weekday. For financial and project purposes, business days are usually the relevant number, which
is why the tool shows both. Months are approximate: dividing by the average month length
(30.44 days) is fine for planning, but exact month arithmetic must be done on the calendar.</p>""",
    formula="""<p>Calendar days = end date − start date (exclusive of the start day). Weeks = days ÷ 7.
Months ≈ days ÷ 30.436875 (the average Gregorian month length, 365.2425 ÷ 12). Business days count
each Monday–Friday encountered, excluding public holidays:</p>
<div class="fml"><code>days         = date(end) − date(start)
weeks        = days / 7
months       ≈ days / 30.436875
business days = count of Mon–Fri between the dates</code></div>
<p>If the end date is before the start date the difference is negative; business days are counted
on the absolute interval.</p>""",
    example="From {start} to {end} is {days} calendar days — {weeks} weeks or about {months} months. "
            "Of those days, {business_days} are weekdays, before subtracting public holidays.",
    mistakes=[
        "<strong>Inclusive vs exclusive counting.</strong> A one-day meeting on a single date has "
        "0 days difference. Add 1 if your policy counts both endpoints.",
        "<strong>Forgetting holidays.</strong> Business days here skip weekends only. Public "
        "holidays must be subtracted separately.",
        "<strong>Using months as exact.</strong> Month lengths vary from 28 to 31 days, so the "
        "month figure is only approximate."
    ],
    faq=[
        ("How do I count days between two dates?",
         "Subtract the earlier date from the later one. For example, 1 January to 31 December is "
         "364 days in a non-leap year."),
        ("Do business days include the start and end dates?",
         "This calculator counts the weekdays strictly between the dates, excluding the start date. "
         "Business-day conventions vary by organisation, so check the policy you are applying."),
        ("How many working days are in a year?",
         "A typical year has 260–262 weekdays. After 10–12 public holidays, most countries have "
         "about 250 working days."),
    ],
    related=["age-calculator", "countdown-days", "business-days", "time-duration"],
    note="Business days skip weekends only; public holidays are not included.",
)


# ---------------------------------------------------------------------------
def _countdown_py(v):
    import datetime as _dt
    today = _dt.date.today().isoformat()
    days = iso_diff(today, v["event_date"])
    d = _dt.date.fromisoformat(str(v["event_date"]))
    weekday = WEEKDAYS_SUN[(d.weekday() + 1) % 7]
    name = (v.get("event_name") or "").strip()
    return {"days": days, "weeks": days / 7, "weekday": weekday,
            "business_days": business_days_between(today, v["event_date"]),
            "event": name or "the event"}


COUNTDOWN = calc(
    slug="countdown-days", name="Countdown Calculator", cat="dates",
    title="Countdown Calculator — Days Until Any Date",
    desc="Count the days, weeks and business days until an event or deadline. Works for holidays, "
         "weddings, trips, exams and project deadlines.",
    h1="Days until calculator",
    lede="Enter an event date to see how many days, weeks and weekdays remain — for holidays, "
         "deadlines, trips or anything else you are counting down to.",
    fields=[txt("event_name", "Event name (optional)", "Christmas", hint="Used in the summary only."),
            dat("event_date", "Event date", "2026-12-25")],
    outs=[("days", "Days remaining", "int"), ("weeks", "Weeks remaining", "num1"),
          ("business_days", "Weekdays remaining", "int"), ("weekday", "The event falls on a", "text")],
    js="""
var now = new Date();
function pad2(n){return (n<10?'0':'')+n;}
var today = now.getFullYear()+'-'+pad2(now.getMonth()+1)+'-'+pad2(now.getDate());
var days = diffDays(today, v.event_date);
var d = isoToUTC(v.event_date);
var WD = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
return {days:days, weeks:days/7, business_days:bizDays(today,v.event_date), weekday:WD[d.getUTCDay()]};
""",
    py=_countdown_py,
    how="""<p>A countdown is simply the difference between today and a future date, so it changes
every day. The calculator runs in your browser, which means it uses the local date on your device,
not the date the page was built — open it again tomorrow and the number will be one lower.</p>
<p>The weekday is useful for planning: a deadline that falls on a Saturday may actually be due the
Friday before, and a holiday trip that starts on a Monday has a different travel pattern from one
that starts midweek. The weekday-remaining figure is the number of Monday–Friday days between now
and the event, excluding public holidays — handy for estimating how many working days you have to
prepare. If the date is in the past, the result is negative, which is a quick way to see how many
days have passed since something happened.</p>""",
    formula="""<p>Days remaining = event date − today, counted as calendar days:</p>
<div class="fml"><code>days     = date(event) − date(today)
weeks    = days / 7
weekdays = count of Monday–Friday between today and the event</code></div>
<p>The browser supplies today's local date, so no page refresh is needed to keep the countdown
correct.</p>""",
    example="{event} falls on {weekday}, which is {days} days from today — about {weeks} weeks. "
            "Excluding weekends, there are {business_days} weekdays before it.",
    mistakes=[
        "<strong>Assuming the page is refreshed daily.</strong> The countdown recalculates from your "
        "device's local date each time it runs, so it stays current without a rebuild.",
        "<strong>Forgetting time zones for deadlines.</strong> A deadline at 23:59 in another "
        "country lands on a different local date. Confirm the time zone in the terms.",
        "<strong>Counting weekdays as working days.</strong> Weekdays remaining excludes weekends "
        "but not public holidays or your own leave."
    ],
    faq=[
        ("How many days until Christmas?",
         "From 22 October 2026 to 25 December 2026 is 64 days. The calculator always counts from "
         "today's local date, so the answer changes as the year progresses."),
        ("Does the countdown include today?",
         "No. The result is the number of full calendar days between today and the event, so an "
         "event tomorrow counts as 1 day."),
        ("How do I count business days until a deadline?",
         "Use the weekdays-remaining figure, which skips Saturdays and Sundays. For a precise "
         "working-day count, also subtract any public holidays that fall before the deadline."),
    ],
    related=["date-difference", "business-days", "time-duration", "age-calculator"],
    note="Uses your device's local date. Weekday counts exclude weekends but not public holidays.",
)


# ---------------------------------------------------------------------------
def _bizdays_py(v):
    start = v["start"]
    n = max(0, int(round(float(v["days"]))))
    count, cur = 0, start
    while count < n:
        cur = iso_add(cur, 1)
        d = dt.date.fromisoformat(cur)
        if d.weekday() < 5:
            count += 1
    calendar_days = iso_diff(start, cur)
    weekends = calendar_days - n
    return {"end_date": cur, "calendar_days": calendar_days, "weekend_days": max(0, weekends)}


BUSINESS_DAYS = calc(
    slug="business-days", name="Business Days Calculator", cat="dates",
    title="Business Days Calculator — Add Working Days to a Date",
    desc="Add or count business days from a start date, skipping weekends. Find the working-day "
         "deadline for contracts, applications and project plans.",
    h1="Business days calculator",
    lede="Start from any date and add a number of business days to find the working-day deadline, "
         "the calendar date it lands on and how many weekend days are skipped.",
    fields=[dat("start", "Start date", "today", hint="Defaults to today."),
            num("days", "Business days to add", 10, unit="days", mn=0, mx=500, step=1)],
    outs=[("end_date", "Resulting date", "date"), ("calendar_days", "Calendar days later", "int"),
          ("weekend_days", "Weekend days skipped", "int")],
    js="""
var n = Math.max(0, Math.round(v.days));
var d = isoToUTC(v.start), count = 0;
while (count < n) {
  d.setUTCDate(d.getUTCDate()+1);
  var wd = d.getUTCDay();
  if (wd !== 0 && wd !== 6) count++;
}
var end = utcToISO(d);
var cal = diffDays(v.start, end);
return {end_date:end, calendar_days:cal, weekend_days:Math.max(0, cal-n)};
""",
    py=_bizdays_py,
    how="""<p>Business-day deadlines are common in contracts, banking and government processes: “within
10 business days” means weekends do not count. Adding business days is a loop rather than a
multiplication, because two extra days can cross zero, one or two weekends depending on which
weekday you start.</p>
<p>This calculator skips Saturdays and Sundays only. It does not know which public holidays apply in
your country or state, so for a legal deadline you must check the holiday calendar and add the
holidays that fall in the period. Many jurisdictions also define “business day” differently (some
include Saturday but not Sunday), so read the wording of the rule you are applying. Start from the
first day that counts as day one — usually the day after a notice is served.</p>""",
    formula="""<p>Starting from the start date, step one calendar day at a time and count only Monday to
Friday until the requested number of business days have passed:</p>
<div class="fml"><code>date ← start
repeat n times:
    date ← date + 1 day
    if date is Mon–Fri: count++
end date = date
calendar days = end date − start date</code></div>
<p>Weekend days skipped is the calendar span minus the business days added.</p>""",
    example="Starting on {start} and adding {days} business days lands on {end_date} — "
            "{calendar_days} calendar days later, because {weekend_days} weekend days were skipped.",
    mistakes=[
        "<strong>Counting the start date as day one.</strong> If a contract says “10 business days "
        "from today”, day one is usually tomorrow, not today.",
        "<strong>Ignoring public holidays.</strong> A holiday inside the window pushes the deadline "
        "out by another day. Add one day per weekday holiday in the period.",
        "<strong>Assuming all countries define business days the same.</strong> Some contracts count "
        "Monday–Saturday, and some count only days the courts or banks are open."
    ],
    faq=[
        ("How many business days are in a month?",
         "A typical month has 20–23 weekdays, depending on its length and where weekends fall. "
         "Subtract public holidays for the true working-day count."),
        ("Does this calculator include Saturdays?",
         "No. It treats Monday–Friday as business days and skips Saturdays and Sundays."),
        ("What does “within 5 business days” mean?",
         "Five working days after the start date, skipping weekends and any public holidays in that "
         "window. Use the calculator to find the exact calendar date, then adjust for holidays."),
    ],
    related=["date-difference", "countdown-days", "age-calculator", "time-duration"],
    note="Skips weekends only. Public holidays and jurisdiction-specific definitions are not included.",
)


# ---------------------------------------------------------------------------
def _duration_py(v):
    def minutes(s):
        h, m = str(s).split(":")
        return int(h) * 60 + int(m)

    start, end = minutes(v["start"]), minutes(v["end"])
    if end <= start:
        end += 24 * 60
    brk = max(0.0, float(v["break"]))
    total = max(0.0, end - start - brk)
    hours = int(total // 60)
    mins = int(round(total - hours * 60))
    if mins == 60:
        hours, mins = hours + 1, 0
    text = f"{hours} hours {mins} minutes" if hours != 1 else f"{hours} hour {mins} minutes"
    return {"duration": text, "hours": total / 60, "minutes": int(r0(total))}


DURATION = calc(
    slug="time-duration", name="Time Duration Calculator", cat="dates",
    title="Time Duration Calculator — Hours Between Two Times",
    desc="Calculate the hours and minutes between two times, minus any break. Handles shifts that "
         "cross midnight and gives decimal hours for timesheets.",
    h1="Time duration calculator",
    lede="Find the hours and minutes between a start and end time, subtract a break, and get the "
         "decimal hours used on timesheets.",
    fields=[tim("start", "Start time", "09:15"), tim("end", "End time", "17:45"),
            num("break", "Unpaid break", 30, unit="minutes", mn=0, mx=480, step=5)],
    outs=[("duration", "Duration", "text"), ("hours", "Decimal hours", "num2"),
          ("minutes", "Total minutes", "int")],
    js="""
function tm(s){ var p=s.split(':'); return parseInt(p[0],10)*60+parseInt(p[1],10); }
var st=tm(v.start), en=tm(v.end);
if (en<=st) en+=24*60;
var br=Math.max(0, v.break);
var total=Math.max(0, en-st-br);
var h=Math.floor(total/60), m=r0(total-h*60);
if(m===60){h+=1;m=0;}
return {duration:h+' hours '+m+' minutes', hours:total/60, minutes:r0(total)};
""",
    py=_duration_py,
    how="""<p>Time duration is the difference between two clock times, expressed in hours and minutes.
When the end time is earlier than the start time, the shift has crossed midnight, so the calculator
adds 24 hours — a 22:00 to 06:00 shift is 8 hours, not a negative number. Breaks are subtracted
afterwards, because an unpaid break is time at work that does not count as paid hours.</p>
<p>Timesheets usually need decimal hours rather than hours and minutes: 7 hours 45 minutes is 7.75
decimal hours. The decimal figure is what payroll systems multiply by the hourly rate, so getting
the conversion right matters — 45 minutes is 0.75 of an hour, not 0.45. If you are paid for an
overnight shift, check whether your employer uses a different midnight-crossing convention, and
remember that daylight-saving changes can add or remove an hour twice a year.</p>""",
    formula="""<p>Convert each time to minutes after midnight, subtract, add 24 hours if the end is
earlier, then remove the break:</p>
<div class="fml"><code>start = hh × 60 + mm
end   = hh × 60 + mm   (if end ≤ start: end += 1440)
minutes = end − start − break
decimal hours = minutes / 60</code></div>
<p>To go the other way, multiply decimal hours by 60 to get minutes: 2.25 hours = 135 minutes.</p>""",
    example="From {start} to {end} with a {break}-minute break is {duration} — {hours} decimal hours, "
            "or {minutes} paid minutes.",
    mistakes=[
        "<strong>Reading minutes as decimals.</strong> 30 minutes is 0.5 hours, not 0.30. Convert by "
        "dividing minutes by 60.",
        "<strong>Forgetting the overnight case.</strong> An end time before the start time means the "
        "next day; otherwise the difference is negative.",
        "<strong>Subtracting breaks twice.</strong> If the shift length already excludes the break, "
        "set the break field to 0."
    ],
    faq=[
        ("How do I calculate hours worked?",
         "Subtract the start time from the end time, add 24 hours if the shift crossed midnight, "
         "then subtract unpaid breaks. Divide minutes by 60 for decimal hours."),
        ("What is 7 hours 45 minutes in decimal?",
         "7.75 hours: 45 ÷ 60 = 0.75. Payroll systems multiply the decimal figure by the hourly "
         "rate."),
        ("Does a 30-minute break get deducted?",
         "Only if it is unpaid. Paid breaks are part of working time and should not be subtracted."),
    ],
    related=["business-days", "date-difference", "countdown-days", "overtime-pay"],
    note="Clock arithmetic only; daylight-saving and payroll rounding rules are not applied.",
)


CALCS = [AGE, DATE_DIFF, COUNTDOWN, BUSINESS_DAYS, DURATION]
