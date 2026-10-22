#!/usr/bin/env python3
"""core.py — data model + HTML/JS renderer for calculators.tekify.xyz.

A calculator is a plain dict built with ``calc(...)``. The important bit is that every
formula lives in exactly two places that are checked against each other:

* ``js`` — a JavaScript function body that takes ``v`` (an object of input values) and
  returns an object keyed like ``outs``. It is what visitors run in the browser.
* ``py`` — a Python function that takes the same ``v`` and returns the same object. It is
  used to render the server-side initial result (no empty box / no layout shift) and to
  cross-check the JS in ``check_formulas.py`` (node runs the JS, Python runs the mirror,
  results must match).

Each page is fully server-rendered: the result shown before any JS runs is the exact
output of ``py`` on the default inputs, so the page is useful with JS disabled too.

Public helpers used by the calc modules:
    num(), sel(), dat(), tim()  field constructors
    calc()                     calculator constructor (validates required keys)
    fnum()                     number -> "1,234.56" (half-up, identical to the JS fnum())
    fmt_date()                 "2026-10-22" -> "Oct 22, 2026"
"""
from __future__ import annotations

import datetime as dt
import json
import math
import re

from engine.sitegen import esc

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BAR_COLORS = ["#1f6feb", "#e0912f", "#3aa657", "#c75c5c", "#8a63d2"]


# --------------------------------------------------------------------------- fields
def num(name, label, default, unit="", mn=0, mx=10**12, step="any", hint="", pre="", post="", show=None):
    return dict(kind="num", name=name, label=label, default=default, unit=unit,
                min=mn, max=mx, step=step, hint=hint, pre=pre, post=post, show=show)


def sel(name, label, options, default=None, hint="", show=None):
    opts = [dict(v=str(v), l=str(l)) for v, l in options]
    if not opts:
        raise ValueError(f"select {name} needs options")
    if default is None:
        default = opts[0]["v"]
    return dict(kind="sel", name=name, label=label, options=opts,
                default=str(default), hint=hint, show=show)


def dat(name, label, default="today", hint="", show=None):
    return dict(kind="date", name=name, label=label, default=default, hint=hint, show=show)


def tim(name, label, default="09:00", hint="", show=None):
    return dict(kind="time", name=name, label=label, default=default, hint=hint, show=show)


def txt(name, label, default="", hint="", show=None):
    return dict(kind="txt", name=name, label=label, default=default, hint=hint, show=show)


REQUIRED = ("slug", "name", "cat", "title", "desc", "h1", "lede", "js", "py",
            "how", "formula", "example", "faq", "related")
BASE = dict(fields=(), outs=(), viz=None, meter=None, js="", py=None, how="",
            formula="", example="", mistakes=(), faq=(), related=(), note="",
            table=None, extra_js="", py_table=None)


def calc(**kw):
    d = dict(BASE)
    d.update(kw)
    for k in ("fields", "outs", "mistakes", "faq", "related"):
        d[k] = list(d[k])
    d["outs"] = [dict(key=o[0], label=o[1], fmt=o[2]) if isinstance(o, (tuple, list))
                 else dict(o) for o in d["outs"]]
    for i, f in enumerate(d["fields"]):
        f = dict(f)
        f.setdefault("hint", "")
        f.setdefault("unit", "")
        f.setdefault("min", None)
        f.setdefault("max", None)
        f.setdefault("step", "any")
        f.setdefault("pre", "")
        f.setdefault("post", "")
        f.setdefault("show", None)
        d["fields"][i] = f
    for k in REQUIRED:
        if not d.get(k):
            raise ValueError(f"calculator {d.get('slug') or kw.get('name')!r}: missing {k}")
    if len(d["faq"]) != 3:
        raise ValueError(f"calculator {d['slug']}: needs exactly 3 FAQ pairs")
    if len(d["mistakes"]) < 2:
        raise ValueError(f"calculator {d['slug']}: needs >=2 common mistakes")
    return d


# --------------------------------------------------------------------------- numbers
def fnum(x, d=2):
    """Format like the browser runtime: half-up rounding, thousands separators."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    if not math.isfinite(x):
        return "—"
    p = 10 ** d
    n = math.floor(x * p + 0.5) / p
    neg = n < 0
    if neg:
        n = -n
    s = f"{n:,.{d}f}" if d else f"{n:,.0f}"
    return ("-" if neg else "") + s


def fmt_date(x):
    try:
        y, m, d = str(x).split("-")
        return f"{MONTHS[int(m) - 1]} {int(d)}, {y}"
    except Exception:
        return str(x)


def fmt_val(kind, x):
    if x is None or x == "":
        return "—"
    if kind == "text":
        return str(x)
    if kind == "date":
        return fmt_date(x)
    if kind == "months":
        return fnum(x, 0) + " months"
    try:
        n = float(x)
    except (TypeError, ValueError):
        return "—"
    if not math.isfinite(n):
        return "—"
    if kind == "money":
        return "$" + fnum(n, 2)
    if kind == "money0":
        return "$" + fnum(n, 0)
    if kind == "num":
        return fnum(n, 2)
    if kind == "num0":
        return fnum(n, 0)
    if kind == "num1":
        return fnum(n, 1)
    if kind == "pct":
        return fnum(n, 2) + "%"
    if kind == "pct1":
        return fnum(n, 1) + "%"
    if kind == "int":
        return fnum(n, 0)
    return str(x)


def _vstr(v):
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


# --------------------------------------------------------------------------- dates
def iso_add(iso_year_month_day, days):
    return (dt.date.fromisoformat(str(iso_year_month_day)) + dt.timedelta(days=int(days))).isoformat()


def iso_diff(a, b):
    """Calendar days from a to b (b - a)."""
    return (dt.date.fromisoformat(str(b)) - dt.date.fromisoformat(str(a))).days


def r0(x):
    """Half-up integer rounding, identical to the JS Math.round used in compute bodies."""
    return int(math.floor(float(x) + 0.5))


def weekday_name(iso):
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][
        dt.date.fromisoformat(str(iso)).weekday()]


def business_days_between(a, b):
    d0 = dt.date.fromisoformat(str(a))
    d1 = dt.date.fromisoformat(str(b))
    if d1 < d0:
        d0, d1 = d1, d0
    n, cur = 0, d0
    while cur < d1:
        cur += dt.timedelta(days=1)
        if cur.weekday() < 5:
            n += 1
    return n


# Shared JS prelude available to every compute body (dates, rounding).
JS_PRELUDE = r"""
function isoToUTC(s){var p=String(s).split('-');return new Date(Date.UTC(+p[0],+p[1]-1,+p[2]));}
function utcToISO(d){var y=d.getUTCFullYear(),m=d.getUTCMonth()+1,dd=d.getUTCDate();
  return y+'-'+(m<10?'0':'')+m+'-'+(dd<10?'0':'')+dd;}
function addDays(s,n){var d=isoToUTC(s);d.setUTCDate(d.getUTCDate()+n);return utcToISO(d);}
function diffDays(a,b){return Math.round((isoToUTC(b)-isoToUTC(a))/86400000);}
function r0(x){return Math.floor(x+0.5);}
function bizDays(a,b){var d0=isoToUTC(a),d1=isoToUTC(b);
  if(d1<d0){var t=d0;d0=d1;d1=t;}
  var n=0,cur=new Date(d0.getTime());
  while(cur<d1){cur.setUTCDate(cur.getUTCDate()+1);
    if(cur.getUTCDay()!==0&&cur.getUTCDay()!==6)n++;}
  return n;}
"""


def js_full(c):
    return JS_PRELUDE + c["js"].strip()


def resolved_fields(c):
    """Field defs with concrete values; 'today' date defaults resolve at build time."""
    out = []
    for f in c["fields"]:
        f = dict(f)
        if f["kind"] == "date":
            if f["default"] == "today":
                f["value"] = dt.date.today().isoformat()
                f["today"] = True
            else:
                f["value"] = f["default"]
                f["today"] = False
        else:
            f["value"] = f["default"]
            f["today"] = False
        out.append(f)
    return out


def defaults(c):
    return {f["name"]: f["value"] for f in resolved_fields(c)}


# --------------------------------------------------------------------------- html
def _field_html(f, values):
    fid = f["name"]
    lab = esc(f["label"])
    if f.get("unit"):
        lab += f' <span class="u">{esc(f["unit"])}</span>'
    hint = f'<p class="hint">{esc(f["hint"])}</p>' if f.get("hint") else ""
    show_attr, hidden = "", ""
    if f.get("show"):
        key, want = f["show"]
        show_attr = f' data-show="{key}={want}"'
        if str(values.get(key, "")) != str(want):
            hidden = ' style="display:none"'
    if f["kind"] == "num":
        attrs = (f'type="number" id="{fid}" name="{fid}" value="{_vstr(f["value"])}" '
                 f'inputmode="decimal" autocomplete="off"')
        if f.get("min") is not None:
            attrs += f' min="{_vstr(f["min"])}"'
        if f.get("max") is not None:
            attrs += f' max="{_vstr(f["max"])}"'
        attrs += f' step="{f.get("step") or "any"}"'
        pre = f'<span class="pre">{esc(f["pre"])}</span>' if f.get("pre") else ""
        post = f'<span class="post">{esc(f["post"])}</span>' if f.get("post") else ""
        ctl = f'<div class="ctl">{pre}<input {attrs}>{post}</div>'
    elif f["kind"] == "sel":
        opts = "".join(
            f'<option value="{esc(o["v"])}"' + (' selected' if o["v"] == f["value"] else "") +
            f'>{esc(o["l"])}</option>' for o in f["options"])
        ctl = f'<div class="ctl"><select id="{fid}" name="{fid}">{opts}</select></div>'
    elif f["kind"] == "date":
        ctl = (f'<div class="ctl"><input type="date" id="{fid}" name="{fid}" '
               f'value="{f["value"]}" autocomplete="off"></div>')
    elif f["kind"] == "time":
        ctl = (f'<div class="ctl"><input type="time" id="{fid}" name="{fid}" '
               f'value="{f["value"]}" autocomplete="off"></div>')
    elif f["kind"] == "txt":
        ctl = (f'<div class="ctl"><input type="text" id="{fid}" name="{fid}" '
               f'value="{esc(_vstr(f["value"]))}" autocomplete="off"></div>')
    else:  # pragma: no cover - constructor guards kinds
        raise ValueError(f"bad field kind {f['kind']}")
    return f'<div class="f"{show_attr}{hidden}><label for="{fid}">{lab}</label>{ctl}{hint}</div>'


def _viz_bar_html(c, r):
    parts = []
    for label, key, kind in c["viz"]:
        try:
            val = abs(float(r.get(key) or 0))
        except (TypeError, ValueError):
            val = 0.0
        parts.append((label, val, fmt_val(kind, r.get(key))))
    total = sum(p[1] for p in parts) or 1.0
    segs = "".join(
        f'<span style="width:{p[1] / total * 100:.2f}%;background:{BAR_COLORS[i % len(BAR_COLORS)]}"></span>'
        for i, p in enumerate(parts))
    leg = " · ".join(f'{esc(p[0])} {esc(p[2])}' for p in parts)
    return f'<div class="viz"><div class="vizbar">{segs}</div><div class="vleg">{leg}</div></div>'


def _meter_cat(m, val):
    for edge, label, _color in m["bands"]:
        if float(val) < float(edge):
            return label
    return m["bands"][-1][1]


def _meter_html(c, r):
    m = c["meter"]
    try:
        val = float(r.get(m["key"]) or 0)
    except (TypeError, ValueError):
        val = 0.0
    mn, mx = float(m["min"]), float(m["max"])
    pct = max(0.0, min(100.0, (val - mn) / (mx - mn) * 100))
    segs, prev = "", mn
    for edge, _label, color in m["bands"]:
        width = (min(float(edge), mx) - prev) / (mx - mn) * 100
        if width > 0:
            segs += f'<span style="width:{width:.2f}%;background:{color}"></span>'
        prev = float(edge)
    cat = _meter_cat(m, val)
    return (f'<div class="viz"><div class="meter"><div class="mtrack">{segs}</div>'
            f'<div class="mpin" style="left:{pct:.2f}%"></div></div>'
            f'<div class="vleg">{esc(m["label"])} '
            f'{esc(fmt_val(m.get("fmt", "num1"), val))} — {esc(cat)}</div></div>')


def render_out(c, r):
    outs = c["outs"]
    main = outs[0]
    html = (f'<div class="main"><span class="big">{esc(fmt_val(main["fmt"], r.get(main["key"])))}</span>'
            f'<span class="lbl">{esc(main["label"])}</span></div>')
    sec = "".join(
        f'<div class="s"><span class="sv">{esc(fmt_val(o["fmt"], r.get(o["key"])))}</span>'
        f'<span class="sl">{esc(o["label"])}</span></div>' for o in outs[1:])
    if sec:
        html += f'<div class="sgrid">{sec}</div>'
    if c.get("viz"):
        html += _viz_bar_html(c, r)
    if c.get("meter"):
        html += _meter_html(c, r)
    if c.get("note"):
        html += f'<p class="rnote">{esc(c["note"])}</p>'
    return f'<div class="result" id="calcout" aria-live="polite">{html}</div>'


def _js_config(c):
    fields = []
    for f in resolved_fields(c):
        fields.append(dict(name=f["name"], kind=f["kind"],
                           default=f["value"], today=f["today"]))
    cfg = dict(fields=fields, outs=c["outs"], note=c.get("note") or "")
    if c.get("viz"):
        cfg["viz"] = [list(p) for p in c["viz"]]
    if c.get("meter"):
        cfg["meter"] = c["meter"]
    return json.dumps(cfg, separators=(",", ":"), ensure_ascii=False)


def render_script(c, script_tag=True):
    extra = ""
    if c.get("extra_js"):
        extra = ("\nwindow.CALC_EXTRA=function(v,r){\n" + c["extra_js"].strip() + "\n};\n")
    body = (f'<script>\nwindow.CALC={_js_config(c)};\n'
            f'window.compute=function(v){{\n{js_full(c)}\n}};\n{extra}</script>')
    if script_tag:
        body += '\n<script src="/assets/calc.js"></script>'
    return body


def render_calcbox(c):
    initial = render_out(c, c["py"](defaults(c)))
    vals = defaults(c)
    fields = "".join(_field_html(f, vals) for f in resolved_fields(c))
    table_block = ""
    if c.get("table"):
        t = c["table"]
        tbody = ""
        if c.get("py_table"):
            try:
                tbody = c["py_table"](defaults(c))
            except Exception:  # pragma: no cover - a table is optional decoration
                tbody = ""
        table_block = (f'<div class="tblblock"><h2>{esc(t["title"])}</h2>'
                       f'<div id="tbl" class="tblout">{tbody}</div></div>')
    return (f'<div class="calcbox">'
            f'<form id="calcform" autocomplete="off" onsubmit="return false">'
            f'<div class="fgrid">{fields}</div></form>'
            f'{initial}{table_block}</div>')


def _example_vars(c, r):
    """Values available to the worked-example / FAQ templates."""
    vals = {}
    for o in c["outs"]:
        vals[o["key"]] = fmt_val(o["fmt"], r.get(o["key"]))
    for f in resolved_fields(c):
        raw = defaults(c).get(f["name"])
        if f["kind"] == "num":
            vals[f["name"]] = fnum(raw, 0) if float(raw).is_integer() else fnum(raw, 2)
        elif f["kind"] == "sel":
            vals[f["name"]] = next((o["l"] for o in f["options"] if o["v"] == str(raw)), str(raw))
        elif f["kind"] == "date":
            vals[f["name"]] = fmt_date(raw)
        else:
            vals[f["name"]] = str(raw)
    return vals


def _fill(template, vals, slug):
    """Fill {placeholders} from output/field values, tolerating small naming drift.

    Generated templates occasionally reference a field by a near-miss name (rate vs
    return_rate). Exact keys win, then case-insensitive, then substring; anything still
    unknown becomes an em dash instead of breaking the build.
    """
    def sub(m):
        k = m.group(1)
        if k in vals:
            return str(vals[k])
        kl = k.lower().replace("-", "_")
        for key in vals:
            if key.lower().replace("-", "_") == kl:
                return str(vals[key])
        for key in vals:
            kk = key.lower().replace("_", "")
            if kk in kl.replace("_", "") or kl.replace("_", "") in kk:
                return str(vals[key])
        for key in vals:
            if kl in key.lower().replace("-", "_"):
                return str(vals[key])
        return "—"

    return re.sub(r"\{([a-zA-Z_][\w]*)\}", sub, template)


TAG_RE = re.compile(r"<[^>]+>")


def word_count(html):
    return len(TAG_RE.sub(" ", html).split())


def page_body(c, cat_name, by_slug):
    r = c["py"](defaults(c))
    vals = _example_vars(c, r)
    example = _fill(c["example"], vals, c["slug"])
    faq_html = '<section class="faq"><h2>Frequently asked questions</h2>'
    for q, a in c["faq"]:
        q2 = _fill(q, vals, c["slug"])
        a2 = _fill(a, vals, c["slug"])
        faq_html += f'<h3>{esc(q2)}</h3><p>{a2}</p>'
    faq_html += "</section>"
    rel = "".join(
        f'<a href="/{by_slug[s]["slug"]}/">{esc(by_slug[s]["name"])}</a>'
        for s in c["related"] if s in by_slug)
    mistakes = "".join(f"<li>{m}</li>" for m in c["mistakes"])
    return f"""<h1>{esc(c["h1"])}</h1>
<p class="lede">{c["lede"]}</p>
{render_calcbox(c)}
<h2>How this calculator works</h2>
{c["how"]}
<h2>The formula</h2>
{c["formula"]}
<h2>Worked example</h2>
<p>{example}</p>
<h2>Common mistakes</h2>
<ul class="mistakes">{mistakes}</ul>
{faq_html}
<div class="rel"><h2>Related calculators</h2><p>{rel} · <a href="/{c["cat"]}/">All {esc(cat_name)} calculators</a></p></div>
{render_script(c)}
"""


# --------------------------------------------------------------------------- assets
CALC_CSS = """
.calcbox{margin:24px 0 6px;border:1px solid var(--line);border-radius:14px;background:var(--card);padding:18px}
.calcbox .fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px 16px}
.f label{display:block;font-size:13px;font-weight:600;color:var(--mut);margin-bottom:5px}
.f label .u{font-weight:400;opacity:.85}
.ctl{display:flex;align-items:center;gap:4px;background:var(--bg);border:1px solid var(--line);border-radius:9px;padding:0 10px}
.ctl:focus-within{border-color:var(--acc);box-shadow:0 0 0 2px rgba(31,111,235,.18)}
.ctl input,.ctl select{border:0;background:transparent;color:var(--fg);font:inherit;font-size:16px;padding:9px 0;width:100%;min-width:0;outline:none}
.ctl select{cursor:pointer}
.ctl .pre,.ctl .post{color:var(--mut);font-size:14px}
.hint{font-size:12px;color:var(--mut);margin:5px 0 0;line-height:1.4}
.result{margin-top:18px;padding-top:16px;border-top:1px dashed var(--line)}
.main{display:flex;flex-direction:column;gap:3px}
.big{font-size:34px;line-height:1.1;font-weight:700;letter-spacing:-.02em;word-break:break-word}
.lbl{font-size:12.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.07em}
.sgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:16px}
.s{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:9px 11px}
.sv{display:block;font-weight:650;font-size:16px;overflow-wrap:anywhere}
.sl{display:block;font-size:12px;color:var(--mut);margin-top:1px}
.viz{margin-top:16px}
.vizbar{display:flex;height:12px;border-radius:6px;overflow:hidden;background:var(--line)}
.vizbar span{display:block;height:100%}
.vleg{font-size:12.5px;color:var(--mut);margin-top:6px}
.meter{position:relative;height:18px;margin:7px 0 2px}
.mtrack{display:flex;height:12px;border-radius:6px;overflow:hidden;background:var(--line);margin-top:3px}
.mtrack span{display:block;height:100%}
.mpin{position:absolute;top:0;width:3px;height:18px;background:var(--fg);border-radius:2px;transform:translateX(-50%);box-shadow:0 0 0 2px var(--bg)}
.rnote{font-size:12.5px;color:var(--mut);margin:12px 0 0}
.tblblock h2{margin-top:28px}
.tblout .tw{margin-top:10px}
.fml{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:12px 0;overflow-x:auto}
.fml code{font:14px/1.55 ui-monospace,SFMono-Regular,Consolas,monospace;white-space:pre-wrap;word-break:break-word}
ul.mistakes{padding-left:22px}
ul.mistakes li{margin:6px 0}
@media(max-width:560px){.big{font-size:28px}.calcbox{padding:14px}}
"""

RUNTIME_JS = r"""
(function () {
  var C = window.CALC;
  if (!C || !C.fields) return;
  var form = document.getElementById('calcform');
  var out = document.getElementById('calcout');
  if (!form || !out) return;
  var MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  function pad2(n) { return (n < 10 ? '0' : '') + n; }
  function todayISO() {
    var d = new Date();
    return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
  }
  function rnd(x, d) { var p = Math.pow(10, d); return Math.floor(x * p + 0.5) / p; }
  function fnum(x, d) {
    if (x === null || x === undefined || x === '' || !isFinite(x)) return '\u2014';
    var n = rnd(Number(x), d), neg = n < 0;
    if (neg) n = -n;
    var s = n.toFixed(d), pp = s.split('.'), ip = pp[0], fp = pp.length > 1 ? '.' + pp[1] : '';
    return (neg ? '-' : '') + ip.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + fp;
  }
  function fdate(x) {
    var p = String(x).split('-');
    if (p.length !== 3 || isNaN(+p[1])) return String(x);
    return MONTHS[(+p[1]) - 1] + ' ' + (+p[2]) + ', ' + p[0];
  }
  function fmt(k, x) {
    if (x === null || x === undefined || x === '') return '\u2014';
    if (k === 'text') return String(x);
    if (k === 'date') return fdate(x);
    var n = Number(x);
    if (!isFinite(n)) return '\u2014';
    if (k === 'money') return '$' + fnum(n, 2);
    if (k === 'money0') return '$' + fnum(n, 0);
    if (k === 'num') return fnum(n, 2);
    if (k === 'num0') return fnum(n, 0);
    if (k === 'num1') return fnum(n, 1);
    if (k === 'pct') return fnum(n, 2) + '%';
    if (k === 'pct1') return fnum(n, 1) + '%';
    if (k === 'int') return fnum(n, 0);
    if (k === 'months') return fnum(n, 0) + ' months';
    return String(x);
  }
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function meterCat(m, val) {
    for (var i = 0; i < m.bands.length; i++) if (val < m.bands[i][0]) return m.bands[i][1];
    return m.bands[m.bands.length - 1][1];
  }
  function outHTML(r) {
    var h = '', sec = '', i, o, s;
    for (i = 0; i < C.outs.length; i++) {
      o = C.outs[i];
      s = esc(fmt(o.fmt, r[o.key]));
      if (i === 0) {
        h += '<div class="main"><span class="big">' + s + '</span><span class="lbl">' + esc(o.label) + '</span></div>';
      } else {
        sec += '<div class="s"><span class="sv">' + s + '</span><span class="sl">' + esc(o.label) + '</span></div>';
      }
    }
    if (sec) h += '<div class="sgrid">' + sec + '</div>';
    if (C.viz) {
      var cols = ['#1f6feb', '#e0912f', '#3aa657', '#c75c5c', '#8a63d2'];
      var tot = 0, vals = [];
      for (i = 0; i < C.viz.length; i++) { var vv = Math.abs(Number(r[C.viz[i][1]]) || 0); vals.push(vv); tot += vv; }
      if (tot <= 0) tot = 1;
      var segs = '', leg = [];
      for (i = 0; i < C.viz.length; i++) {
        segs += '<span style="width:' + (vals[i] / tot * 100).toFixed(2) + '%;background:' + cols[i % cols.length] + '"></span>';
        leg.push(esc(C.viz[i][0]) + ' ' + esc(fmt(C.viz[i][2], r[C.viz[i][1]])));
      }
      h += '<div class="viz"><div class="vizbar">' + segs + '</div><div class="vleg">' + leg.join(' \u00b7 ') + '</div></div>';
    }
    if (C.meter) {
      var m = C.meter, val = Number(r[m.key]) || 0, mn = m.min, mx = m.max;
      var pct = Math.max(0, Math.min(100, (val - mn) / (mx - mn) * 100));
      var mg = '', prev = mn;
      for (i = 0; i < m.bands.length; i++) {
        var w = (Math.min(m.bands[i][0], mx) - prev) / (mx - mn) * 100;
        if (w > 0) mg += '<span style="width:' + w.toFixed(2) + '%;background:' + m.bands[i][2] + '"></span>';
        prev = m.bands[i][0];
      }
      h += '<div class="viz"><div class="meter"><div class="mtrack">' + mg + '</div>' +
           '<div class="mpin" style="left:' + pct.toFixed(2) + '%"></div></div>' +
           '<div class="vleg">' + esc(m.label) + ' ' + esc(fmt(m.fmt || 'num1', val)) +
           ' \u2014 ' + esc(meterCat(m, val)) + '</div></div>';
    }
    if (C.note) h += '<p class="rnote">' + esc(C.note) + '</p>';
    return h;
  }
  function collect() {
    var v = {};
    for (var i = 0; i < C.fields.length; i++) {
      var f = C.fields[i], el = document.getElementById(f.name);
      if (!el) continue;
      if (f.kind === 'num') {
        var x = parseFloat(el.value);
        v[f.name] = isFinite(x) ? x : (Number(f.default) || 0);
      } else {
        v[f.name] = el.value;
      }
    }
    return v;
  }
  function applyShow() {
    var els = form.querySelectorAll('[data-show]');
    for (var i = 0; i < els.length; i++) {
      var spec = els[i].getAttribute('data-show').split('=');
      var ctrl = document.getElementById(spec[0]);
      var on = ctrl ? ctrl.value === spec[1] : true;
      els[i].style.display = on ? '' : 'none';
    }
  }
  function render() {
    if (typeof window.compute !== 'function') return;
    applyShow();
    var v, r;
    try { v = collect(); r = window.compute(v); } catch (e) { return; }
    if (!r) return;
    try { out.innerHTML = outHTML(r); } catch (e) { }
    if (typeof window.CALC_EXTRA === 'function') {
      try { window.CALC_EXTRA(v, r); } catch (e) { }
    }
  }
  for (var i = 0; i < C.fields.length; i++) {
    if (C.fields[i].today) {
      var el = document.getElementById(C.fields[i].name);
      if (el && el.type === 'date') el.value = todayISO();
    }
  }
  form.addEventListener('input', render);
  form.addEventListener('change', render);
  render();
})();
"""


def table_html(headers, rows, cls=""):
    """Same markup as engine.sitegen.table, usable from calc table builders."""
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'
