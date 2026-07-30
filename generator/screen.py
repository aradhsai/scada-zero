"""T-101 mimic — P&ID on a dark control-room background.

Design rules held to throughout:
  * Pipes read as tubes, not lines. Each run is drawn three times — a dark
    casing, a mid body, and an offset highlight — which is the cheapest way to
    get cylindrical shading in flat SVG.
  * Routing is orthogonal with proper radiused elbows. Diagonal pipe is the
    fastest way to make a mimic look like a drawing tool rather than a plant.
  * Symbols follow ISA convention: centrifugal pumps as circle + volute,
    isolation valves as bowties, check valves with a flow flap, instruments as
    balloons with tag numbers.
  * Colour carries one meaning each. Green is running, amber is warning, red is
    alarm, cyan is a setpoint. Nothing decorative uses those four.
"""
from tags import tag_id, vref

W, H = 1600, 900
BG      = "#0b0f14"
PANEL   = "#131a22"
HAIR    = "#1e2833"
INK     = "#e6edf3"
MUTED   = "#8b98a5"
FAINT   = "#5a6672"
PIPE_D  = "#232d38"   # casing
PIPE_M  = "#41505f"   # body
PIPE_H  = "#6a7c8d"   # highlight
FLUID   = "#2f81f7"
GREEN   = "#3fb950"
AMBER   = "#d29922"
RED     = "#f85149"
CYAN    = "#39c5cf"

# tank geometry
TX, TY, TW, TH = 600, 210, 250, 360      # tank body
RY = 26                                   # ellipse cap radius

items = {}

def add(sid, gtype, prop, name=None):
    items[sid] = {"id": sid, "type": gtype, "name": name or sid,
                  "property": prop, "label": "", "hide": False, "lock": False}

def pipe(d, wide=16):
    """One pipe run, drawn as casing + body + highlight."""
    hl = wide * 0.22
    return (f'<path d="{d}" fill="none" stroke="{PIPE_D}" stroke-width="{wide+4}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{PIPE_M}" stroke-width="{wide}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{PIPE_H}" stroke-width="{hl}" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="0.55" '
            f'transform="translate(0,-{wide*0.26:.1f})"/>')

def flow(sid, d, wide=9, dur="1.1s", rev=False):
    """Animated fluid overlay. Shown only while the line is actually flowing —
    a mimic that animates a dead line teaches operators to ignore it."""
    off = "24;0" if not rev else "0;24"
    return (f'<path id="{sid}" type="svg-ext-shapes" d="{d}" fill="none" stroke="{FLUID}" stroke-width="{wide}" '
            f'stroke-linecap="round" stroke-dasharray="10 14" opacity="0.95">'
            f'<animate attributeName="stroke-dashoffset" values="{off}" dur="{dur}" '
            f'repeatCount="indefinite"/></path>')

def txt(x, y, s, size=13, fill=MUTED, anchor="start", weight="400", family="mono", sid=None, ls="0"):
    """Static label, or — when sid is given — a bound value gauge.

    FUXA identifies a gauge in the DOM by a `type` attribute on a <g> wrapper,
    with the <text> nested inside. A bare <text id=...> is never bound, however
    correct the project JSON is. Taken from the shipped project.demo.fuxap;
    it is not in the documentation.
    """
    fam = "'IBM Plex Mono',ui-monospace,monospace" if family == "mono" else "Inter,Segoe UI,sans-serif"
    body = (f'<text{{I}} x="{x}" y="{y}" font-family="{fam}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" letter-spacing="{ls}">{s}</text>')
    if sid:
        return (f'<g id="{sid}" type="svg-ext-value" font-family="{fam}" font-size="{size}" '
                f'fill="{fill}" text-anchor="{anchor}">' + body.replace("{I}", f' id="{sid}_t"') + '</g>')
    return body.replace("{I}", "")

def panel(x, y, w, h, r=10):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{PANEL}" '
            f'stroke="{HAIR}" stroke-width="1"/>')

def balloon(x, y, tag, sub=""):
    """ISA instrument balloon."""
    s = (f'<circle cx="{x}" cy="{y}" r="21" fill="{PANEL}" stroke="{FAINT}" stroke-width="1.4"/>'
         f'<line x1="{x-21}" y1="{y}" x2="{x+21}" y2="{y}" stroke="{FAINT}" stroke-width="1"/>')
    s += txt(x, y-5, tag, 11, MUTED, "middle", "500")
    s += txt(x, y+14, sub, 11, FAINT, "middle")
    return s


def pump(x, y, tag, sid_body, sid_imp, sid_led, mirror=False):
    """ISA centrifugal pump: volute circle + discharge trapezoid + base.
    Impeller is a separate group so it can be spun independently of the casing."""
    s = f'<g id="{sid_body}-g">'
    # base plinth
    s += f'<rect x="{x-34}" y="{y+26}" width="68" height="9" rx="2" fill="{PIPE_D}"/>'
    # volute (discharge cone) pointing up
    s += (f'<path d="M {x-15} {y-6} L {x-11} {y-40} L {x+11} {y-40} L {x+15} {y-6} Z" '
          f'fill="{PIPE_M}" stroke="{PIPE_D}" stroke-width="2"/>')
    # casing
    s += (f'<circle id="{sid_body}" type="svg-ext-shapes" cx="{x}" cy="{y}" r="30" fill="{PIPE_M}" '
          f'stroke="{PIPE_D}" stroke-width="2.5"/>')
    s += f'<circle cx="{x}" cy="{y}" r="30" fill="url(#pumpShade)" opacity="0.8"/>'
    # impeller — three curved vanes
    s += f'<g id="{sid_imp}" type="svg-ext-shapes"'+'>'
    for a in (0, 120, 240):
        s += (f'<path d="M {x} {y} q 13 -6 19 -13" fill="none" stroke="{INK}" '
              f'stroke-width="3.5" stroke-linecap="round" opacity="0.75" '
              f'transform="rotate({a} {x} {y})"/>')
    s += f'<circle cx="{x}" cy="{y}" r="5" fill="{INK}" opacity="0.8"/>'
    s += '</g>'
    # run LED
    s += f'<circle id="{sid_led}" type="svg-ext-shapes" cx="{x+22}" cy="{y-22}" r="6" fill="{FAINT}"/>'
    s += txt(x, y+52, tag, 13, INK, "middle", "600")
    s += '</g>'
    return s

def valve_iso(x, y, sid=None, vert=False):
    """Isolation valve — ISA bowtie."""
    i = f' id="{sid}" type="svg-ext-shapes"' if sid else ""
    if vert:
        b = (f'<path{i} d="M {x-13} {y-11} L {x+13} {y-11} L {x-13} {y+11} L {x+13} {y+11} Z" '
             f'fill="{PIPE_M}" stroke="{PIPE_H}" stroke-width="1.6"/>')
        st = f'<line x1="{x}" y1="{y-11}" x2="{x}" y2="{y+11}" stroke="{PIPE_D}" stroke-width="1"/>'
    else:
        b = (f'<path{i} d="M {x-11} {y-13} L {x-11} {y+13} L {x+11} {y-13} L {x+11} {y+13} Z" '
             f'fill="{PIPE_M}" stroke="{PIPE_H}" stroke-width="1.6"/>')
        st = f'<line x1="{x-11}" y1="{y}" x2="{x+11}" y2="{y}" stroke="{PIPE_D}" stroke-width="1"/>'
    return b + st

def valve_check(x, y):
    """Check valve — bowtie with flap, flow left to right."""
    s = valve_iso(x, y)
    s += (f'<line x1="{x+11}" y1="{y-13}" x2="{x+2}" y2="{y+9}" stroke="{INK}" '
          f'stroke-width="2.2" opacity="0.8"/>')
    return s

def valve_control(x, y, sid_body):
    """Modulating control valve — bowtie plus diaphragm actuator."""
    s = (f'<line x1="{x}" y1="{y-13}" x2="{x}" y2="{y-30}" stroke="{PIPE_H}" stroke-width="3"/>'
         f'<path d="M {x-19} {y-30} a 19 13 0 0 1 38 0 Z" fill="{PIPE_M}" '
         f'stroke="{PIPE_H}" stroke-width="1.6"/>')
    s += valve_iso(x, y, sid_body)
    return s


def build():
    """Compose the full view. Returns (svgcontent, items)."""
    d = []
    a = d.append

    # ---------- defs ----------
    a('<defs>')
    a(f'<linearGradient id="fluidGrad" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0" stop-color="#1f6feb"/><stop offset="0.45" stop-color="#4a9eff"/>'
      f'<stop offset="1" stop-color="#1f6feb"/></linearGradient>')
    a(f'<radialGradient id="pumpShade" cx="0.35" cy="0.3" r="0.8">'
      f'<stop offset="0" stop-color="#ffffff" stop-opacity="0.18"/>'
      f'<stop offset="1" stop-color="#000000" stop-opacity="0.35"/></radialGradient>')
    a(f'<linearGradient id="shellGrad" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0" stop-color="#1a2430"/><stop offset="0.3" stop-color="#2b3947"/>'
      f'<stop offset="1" stop-color="#16202a"/></linearGradient>')
    # tank interior clip — the level fill is masked to this
    a(f'<clipPath id="tankClip"><path d="M {TX} {TY} '
      f'a {TW/2} {RY} 0 0 0 {TW} 0 v {TH} a {TW/2} {RY} 0 0 1 -{TW} 0 Z"/></clipPath>')
    a('</defs>')

    # ---------- background ----------
    a(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    for gx in range(0, W, 40):
        a(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{H}" stroke="{HAIR}" stroke-width="0.5" opacity="0.35"/>')
    for gy in range(0, H, 40):
        a(f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}" stroke="{HAIR}" stroke-width="0.5" opacity="0.35"/>')

    # ---------- header ----------
    a(f'<rect x="0" y="0" width="{W}" height="64" fill="{PANEL}"/>')
    a(f'<line x1="0" y1="64" x2="{W}" y2="64" stroke="{HAIR}" stroke-width="1.5"/>')
    a(f'<rect x="0" y="0" width="5" height="64" fill="{FLUID}"/>')
    a(txt(28, 29, "NORTHWIND TERMINAL &#183; ROTTERDAM", 12, MUTED, "start", "500", ls="2.6"))
    a(txt(28, 50, "T-101 TRANSFER SYSTEM", 19, INK, "start", "600", "sans"))

    a(txt(1120, 30, "MODE", 10, FAINT, "middle", "500", ls="1.6"))
    a(txt(1120, 51, "AUTO", 16, GREEN, "middle", "600", sid="v_mode"))
    a(txt(1240, 30, "DUTY", 10, FAINT, "middle", "500", ls="1.6"))
    a(txt(1240, 51, "A", 16, INK, "middle", "600", sid="v_duty"))

    # alarm banner — hidden unless something is actually in alarm
    a(f'<g id="alarmBanner" type="svg-ext-shapes"><rect x="1320" y="14" width="250" height="36" rx="6" '
      f'fill="#3d1418" stroke="{RED}" stroke-width="1.5"/>')
    a(txt(1445, 38, "&#9650;  LEVEL ALARM", 14, RED, "middle", "600"))
    a('</g>')

    # ============================ PIPING ============================
    # Inlet header: left edge -> control valve -> elbow down -> tank top
    inlet = f"M 60 250 H 300 M 340 250 H 470 Q 490 250 490 270 V 300 Q 490 320 510 320 H {TX+TW/2-90}"
    inlet_to_tank = f"M {TX+TW/2} 150 V {TY-6}"
    a(pipe(inlet))
    a(pipe(f"M {TX+TW/2-90} 320 Q {TX+TW/2} 320 {TX+TW/2} 280 V {TY-4}"))
    a(flow("flowIn", inlet, 9))
    a(flow("flowIn2", f"M {TX+TW/2-90} 320 Q {TX+TW/2} 320 {TX+TW/2} 280 V {TY-4}", 9))

    # Suction: tank bottom -> down -> header right -> two branches up to pumps
    suction = f"M {TX+TW/2} {TY+TH+RY} V 640 Q {TX+TW/2} 665 {TX+TW/2+25} 665 H 960"
    a(pipe(suction))
    a(flow("flowSuc", suction, 9))
    # branch A up, branch B stays low
    brA = "M 960 665 Q 985 665 985 640 V 545 Q 985 520 1010 520 H 1050"
    brB = "M 960 665 H 1050"
    a(pipe(brA)); a(pipe(brB))
    a(flow("flowSucA", brA, 8)); a(flow("flowSucB", brB, 8))

    # Pump discharge -> check valve -> iso -> common header -> to berth
    disA = "M 1130 520 H 1210 Q 1235 520 1235 545 V 660"
    disB = "M 1130 665 H 1235"
    a(pipe(disA)); a(pipe(disB))
    a(flow("flowDisA", disA, 8)); a(flow("flowDisB", disB, 8))
    hdr = "M 1235 665 H 1520"
    a(pipe(hdr, 18))
    a(flow("flowHdr", hdr, 10))
    # destination arrow
    a(f'<path d="M 1520 655 L 1548 665 L 1520 675 Z" fill="{PIPE_H}"/>')
    a(txt(1540, 700, "TO BERTH 4", 12, MUTED, "end", "500"))

    # ============================ TANK ============================
    a(f'<path d="M {TX} {TY} a {TW/2} {RY} 0 0 0 {TW} 0 v {TH} a {TW/2} {RY} 0 0 1 -{TW} 0 Z" '
      f'fill="url(#shellGrad)" stroke="{PIPE_H}" stroke-width="2.5"/>')
    # level fill — a tall rect clipped to the shell, driven down the Y axis by level
    a(f'<g clip-path="url(#tankClip)"><rect id="levelFill" type="svg-ext-shapes" x="{TX}" y="{TY}" '
      f'width="{TW}" height="{TH+RY*2}" fill="url(#fluidGrad)" opacity="0.85"/>'
      f'<ellipse id="levelSurface" type="svg-ext-shapes" cx="{TX+TW/2}" cy="{TY}" rx="{TW/2}" ry="{RY}" '
      f'fill="#6cb6ff" opacity="0.55"/></g>')
    # top cap drawn over the fill so the vessel reads as closed
    a(f'<ellipse cx="{TX+TW/2}" cy="{TY}" rx="{TW/2}" ry="{RY}" fill="#1a2430" '
      f'stroke="{PIPE_H}" stroke-width="2.5"/>')
    a(txt(TX+TW/2, TY+TH+70, "T-101", 17, INK, "middle", "600"))
    a(txt(TX+TW/2, TY+TH+90, "35.4 m&#179; &#183; 5.0 m", 11, FAINT, "middle"))

    # level scale + setpoint markers
    sx = TX + TW + 26
    a(f'<line x1="{sx}" y1="{TY}" x2="{sx}" y2="{TY+TH}" stroke="{FAINT}" stroke-width="1.5"/>')
    for pct in range(0, 101, 10):
        yy = TY + TH - (TH * pct / 100)
        ln = 12 if pct % 50 == 0 else 6
        a(f'<line x1="{sx}" y1="{yy}" x2="{sx+ln}" y2="{yy}" stroke="{FAINT}" stroke-width="1.2"/>')
        if pct % 50 == 0:
            a(txt(sx+18, yy+4, str(pct), 11, FAINT))
    for pct, lab, col in ((90, "HH", RED), (80, "H", AMBER), (20, "L", AMBER), (10, "LL", RED)):
        yy = TY + TH - (TH * pct / 100)
        a(f'<line x1="{TX-16}" y1="{yy}" x2="{sx}" y2="{yy}" stroke="{col}" '
          f'stroke-width="1.4" stroke-dasharray="7 5" opacity="0.75"/>')
        a(txt(TX-22, yy+4, lab, 11, col, "end", "600"))

    # big level readout on the tank
    a(txt(TX+TW/2, TY+TH/2-6, "0.0", 46, INK, "middle", "600", "sans", sid="v_level"))
    a(txt(TX+TW/2, TY+TH/2+22, "% LEVEL", 11, MUTED, "middle", "500", ls="2"))
    return d, a


def build_equipment(d, a):
    # ---- inlet control valve XV-101 ----
    a(valve_control(320, 250, "xv101"))
    a(balloon(320, 176, "LIC", "101"))
    a(f'<line x1="320" y1="197" x2="320" y2="220" stroke="{FAINT}" stroke-width="1" stroke-dasharray="4 3"/>')
    a(txt(320, 300, "XV-101", 12, INK, "middle", "600"))
    a(txt(320, 318, "INLET", 10, FAINT, "middle"))
    a(txt(70, 232, "FROM TANK FARM", 12, MUTED, "start", "500"))

    # ---- pumps ----
    a(pump(1090, 520, "P-101A", "pumpA", "impA", "ledA"))
    a(pump(1090, 665, "P-101B", "pumpB", "impB", "ledB"))
    # suction isolation + discharge check/iso per pump
    a(valve_iso(1030, 520)); a(valve_check(1160, 520)); a(valve_iso(1195, 520))
    a(valve_iso(1030, 665)); a(valve_check(1160, 665)); a(valve_iso(1195, 665))

    # ---- instrument balloons ----
    a(balloon(TX+TW/2, 128, "LT", "101"))
    a(f'<line x1="{TX+TW/2}" y1="149" x2="{TX+TW/2}" y2="{TY-4}" stroke="{FAINT}" '
      f'stroke-width="1" stroke-dasharray="4 3"/>')
    a(balloon(1380, 600, "FT", "101"))
    a(f'<line x1="1380" y1="621" x2="1380" y2="655" stroke="{FAINT}" stroke-width="1" stroke-dasharray="4 3"/>')

    # ---- KPI strip ----
    kp = [("INLET FLOW", "v_inflow", "m&#179;/h", 40),
          ("DISCHARGE",  "v_outflow", "m&#179;/h", 300),
          ("VOLUME",     "v_volume",  "m&#179;",   560),
          ("TRANSFERRED","v_total",   "m&#179;",   820),
          ("XV-101",     "v_valve",   "%",        1080),
          ("DUTY HOURS", "v_hours",   "h",        1340)]
    a(panel(24, 756, 1552, 116, 12))
    for label, sid, unit, x in kp:
        a(txt(x+18, 786, label, 10, FAINT, "start", "500", ls="1.8"))
        a(txt(x+18, 830, "0", 30, INK, "start", "600", "sans", sid=sid))
        a(txt(x+18, 852, unit, 11, MUTED, "start"))
        if x > 40:
            a(f'<line x1="{x-8}" y1="772" x2="{x-8}" y2="856" stroke="{HAIR}" stroke-width="1"/>')

    # ---- pump status cards ----
    for i, (tag, sid_sp, sid_hr, sid_st, y) in enumerate(
            [("P-101A", "v_spdA", "v_hrsA", "v_stA", 452),
             ("P-101B", "v_spdB", "v_hrsB", "v_stB", 597)]):
        a(panel(1300, y, 268, 118, 10))
        a(txt(1320, y+28, tag, 14, INK, "start", "600"))
        a(f'<rect id="{sid_st}-bg" x="1470" y="{y+13}" width="80" height="24" rx="12" '
          f'fill="#1c2530" stroke="{HAIR}" stroke-width="1"/>')
        a(txt(1510, y+30, "STOPPED", 10, MUTED, "middle", "600", sid=sid_st))
        a(txt(1320, y+58, "SPEED", 10, FAINT, "start", "500", ls="1.4"))
        a(txt(1320, y+86, "0", 24, INK, "start", "600", "sans", sid=sid_sp))
        a(txt(1372, y+86, "%", 12, MUTED, "start"))
        a(txt(1440, y+58, "RUNTIME", 10, FAINT, "start", "500", ls="1.4"))
        a(txt(1440, y+86, "0", 24, INK, "start", "600", "sans", sid=sid_hr))
        a(txt(1510, y+86, "h", 12, MUTED, "start"))

    # ---- trend chart ----
    # HTML gauges are not plain SVG: FUXA injects its Angular component into a
    # <foreignObject> whose id is "H-" + the item id, sitting beside a backing
    # <rect>, all inside a <g> carrying the type attribute. Structure taken from
    # the chart element in project.demo.fuxap.
    CX, CY, CW, CH = 24, 596, 530, 150
    a(f'<g id="HXC_trend" type="svg-ext-html_chart" font-size="12" font-family="sans-serif">'
      f'<rect x="{CX}" y="{CY}" width="{CW}" height="{CH}" rx="10" id="svg_trendbg" '
      f'fill="{PANEL}" stroke="{HAIR}" stroke-width="1"/>'
      f'<foreignObject x="{CX}" y="{CY}" width="{CW}" height="{CH}" id="H-HXC_trend">'
      f'<DIV style="width:100%;height:100%;vector-effect:non-scaling-stroke"></DIV>'
      f'</foreignObject></g>')
    a(txt(CX + 16, CY - 10, "LEVEL &#183; INFLOW &#183; DISCHARGE  \u2014  LIVE TREND", 10, FAINT, "start", "500", ls="1.8"))

    # ---- setpoint readouts ----
    a(panel(24, 452, 250, 118, 10))
    a(txt(44, 480, "SETPOINTS", 10, FAINT, "start", "500", ls="1.8"))
    a(txt(44, 512, "START", 11, MUTED, "start"))
    a(txt(180, 512, "78", 15, CYAN, "end", "600", sid="v_spStart"))
    a(txt(196, 512, "%", 11, MUTED, "start"))
    a(txt(44, 540, "STOP", 11, MUTED, "start"))
    a(txt(180, 540, "32", 15, CYAN, "end", "600", sid="v_spStop"))
    a(txt(196, 540, "%", 11, MUTED, "start"))
    return d


# --------------------------------------------------------------------------
# Bindings. Gauge types and action names are taken from the built 1.3.3 client
# bundle and hmi.ts, not guessed.
# --------------------------------------------------------------------------
def _val(tag, digits=1, ranges=None):
    p = {"permission": 0, "options": {"decimals": digits},
         "ranges": ranges or [], "events": [], "actions": []}
    p.update(vref(tag))
    return p

def _act(tag, atype, options, rng=None):
    a = {"bitmask": 0, "range": rng or {"min": 1, "max": 1},
         "type": atype, "options": options}
    a.update(vref(tag))
    return a

def build_items():
    it = {}
    def V(sid, tag, digits=1, ranges=None):
        it[sid] = {"id": sid, "type": "svg-ext-value", "name": sid,
                   "property": _val(tag, digits, ranges), "label": "", "hide": False, "lock": False}
    def S(sid, prop):
        it[sid] = {"id": sid, "type": "svg-ext-shapes", "name": sid,
                   "property": prop, "label": "", "hide": False, "lock": False}

    # --- numeric readouts ---
    V("v_level", "level", 1); V("v_inflow", "inflow", 1); V("v_outflow", "outflow", 1)
    V("v_volume", "volume", 1); V("v_total", "totaliser", 0); V("v_valve", "valvePos", 0)
    V("v_spdA", "pAspd", 0); V("v_spdB", "pBspd", 0)
    V("v_hrsA", "pAhrs", 1); V("v_hrsB", "pBhrs", 1); V("v_hours", "pAhrs", 1)
    V("v_spStart", "spStart", 0); V("v_spStop", "spStop", 0)
    V("v_mode", "mode", 0); V("v_duty", "duty", 0)

    # --- tank level fill: slide the clipped rect down the Y axis ---
    S("levelFill", {**vref("level"), "permission": 0, "ranges": [], "events": [],
        "actions": [_act("level", "shapes.action-moveByTags",
                         {"axis": "y", "valueMin": 0, "valueMax": 100,
                          "positionMin": TH, "positionMax": 0, "duration": 400},
                         {"min": 0, "max": 100})]})
    S("levelSurface", {**vref("level"), "permission": 0, "ranges": [], "events": [],
        "actions": [_act("level", "shapes.action-moveByTags",
                         {"axis": "y", "valueMin": 0, "valueMax": 100,
                          "positionMin": TH, "positionMax": 0, "duration": 400},
                         {"min": 0, "max": 100})]})

    # --- pump run state: casing colour + LED + spinning impeller ---
    for sid_body, sid_imp, sid_led, sid_st, run_tag, flt_tag in (
            ("pumpA", "impA", "ledA", "v_stA", "pArun", "pAflt"),
            ("pumpB", "impB", "ledB", "v_stB", "pBrun", "pBflt")):
        S(sid_body, {**vref(run_tag), "permission": 0, "events": [],
            "ranges": [{"min": 0, "max": 0, "color": PIPE_M, "stroke": PIPE_D, "text": "", "type": "range", "style": 0},
                       {"min": 1, "max": 1, "color": "#1d3f28", "stroke": GREEN, "text": "", "type": "range", "style": 0}],
            "actions": []})
        S(sid_led, {**vref(run_tag), "permission": 0, "events": [],
            "ranges": [{"min": 0, "max": 0, "color": FAINT, "stroke": FAINT, "text": "", "type": "range", "style": 0},
                       {"min": 1, "max": 1, "color": GREEN, "stroke": GREEN, "text": "", "type": "range", "style": 0}],
            "actions": []})
        # impeller spins only while running
        S(sid_imp, {**vref(run_tag), "permission": 0, "ranges": [], "events": [],
            "actions": [_act(run_tag, "shapes.action-clockwise", {"duration": 900}, {"min": 1, "max": 1}),
                        _act(run_tag, "shapes.action-stop", {}, {"min": 0, "max": 0})]})
        # status pill text + fault takes precedence
        it[sid_st] = {"id": sid_st, "type": "svg-ext-value", "name": sid_st, "label": "",
            "hide": False, "lock": False,
            "property": {**vref(run_tag), "permission": 0, "options": {},
                # "step", not "range": step substitutes the text, range only
                # recolours and leaves the raw number showing.
                "ranges": [{"min": "0", "max": "0", "text": "STOPPED", "type": "step", "color": MUTED},
                           {"min": "1", "max": "1", "text": "RUNNING", "type": "step", "color": GREEN}],
                "events": [], "actions": []}}

    # --- inlet control valve: colour by position ---
    S("xv101", {**vref("valvePos"), "permission": 0, "events": [],
        "ranges": [{"min": 0, "max": 1, "color": PIPE_M, "stroke": PIPE_H, "text": "", "type": "range", "style": 0},
                   {"min": 1, "max": 100, "color": "#14304d", "stroke": FLUID, "text": "", "type": "range", "style": 0}],
        "actions": []})

    # --- flow overlays: visible only when the line is actually moving ---
    for sid, tag in (("flowIn", "inflow"), ("flowIn2", "inflow"), ("flowSuc", "outflow"),
                     ("flowHdr", "outflow")):
        S(sid, {**vref(tag), "permission": 0, "ranges": [], "events": [],
            "actions": [_act(tag, "shapes.action-hide", {}, {"min": -1, "max": 0.4}),
                        _act(tag, "shapes.action-show", {}, {"min": 0.4, "max": 99999})]})
    for sid, tag in (("flowSucA", "pAspd"), ("flowDisA", "pAspd"),
                     ("flowSucB", "pBspd"), ("flowDisB", "pBspd")):
        S(sid, {**vref(tag), "permission": 0, "ranges": [], "events": [],
            "actions": [_act(tag, "shapes.action-hide", {}, {"min": -1, "max": 1}),
                        _act(tag, "shapes.action-show", {}, {"min": 1, "max": 101})]})

    # --- trend chart: property.id points at the entry in project.charts ---
    it["HXC_trend"] = {"id": "HXC_trend", "type": "svg-ext-html_chart",
                       "name": "T-101 Trend", "label": "HtmlChart",
                       "hide": False, "lock": False,
                       "property": {"id": "chart_t101", "type": "realtime1"}}

    # --- alarm banner: hidden when quiet, blinking when not ---
    S("alarmBanner", {**vref("aAny"), "permission": 0, "ranges": [], "events": [],
        "actions": [_act("aAny", "shapes.action-hide", {}, {"min": 0, "max": 0}),
                    _act("aAny", "shapes.action-show", {}, {"min": 1, "max": 1}),
                    _act("aAny", "shapes.action-blink",
                         {"fillA": "#3d1418", "fillB": "#6b1f26", "strokeA": RED,
                          "strokeB": "#ff7b72", "interval": 700}, {"min": 1, "max": 1})]})
    return it


def render():
    d, a = build()
    build_equipment(d, a)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}">' + "".join(d) + '</svg>')
    return svg, build_items()
