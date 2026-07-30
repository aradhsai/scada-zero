"""Generate the whole FUXA project and POST it.

The screen is an output, not a place decisions live — same principle as the
Ignition fleet work. Edit tags.py or screen.py, re-run this, and the HMI is
rebuilt identically. Nothing is clicked.
"""
import json, sys, urllib.request
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from tags import TAGS, BASE, tag_id, DEV_NAME
import screen

FUXA = "http://127.0.0.1:1881"
DEV_ID = DEV_NAME   # FUXA keys the devices dict by name
VIEW_ID = "v_t101"

def device():
    tags = {}
    for key, suffix, ttype, unit, digits, desc in TAGS:
        tid = tag_id(key)
        tags[tid] = {
            # id and name deliberately identical: FUXA's own demo project has
            # them the same, so it is not possible to tell from it whether a
            # gauge reference resolves by id or by name. Making them equal
            # removes the question. The topic lives in `address`.
            "id": tid, "name": tid, "label": key,
            "type": ttype, "address": f"{BASE}/{suffix}", "memaddress": "",
            "options": {"subs": []}, "format": digits, "description": desc,
            "init": "", "value": "",
            "daq": {"enabled": True, "changed": True, "interval": 60, "restored": False},
        }
    return {
        "id": DEV_NAME, "name": DEV_NAME, "enabled": True, "type": "MQTTclient",
        "polling": 500,
        "property": {"address": "mqtt://mosquitto:1883", "clientId": "fuxa-t101",
                     "uid": "", "pwd": "", "options": ""},
        "tags": tags,
    }

def view():
    svg, items = screen.render()
    variables = {}   # FUXA's own demo project leaves this empty; bindings
                     # resolve through variableId/variableSrc instead.
    return {
        "id": VIEW_ID, "name": "T-101 Rotterdam", "type": "svg",
        "profile": {"width": screen.W, "height": screen.H,
                    "bkcolor": screen.BG, "margin": 0, "align": 0},
        "items": items, "variables": variables, "svgcontent": svg,
        "property": {"events": []},
    }

def project():
    return {
        "version": "1.01", "name": "fuxa-lab",
        "server": {"id": "s_fuxa", "name": "FUXA Server", "enabled": True,
                   "type": "FuxaServer", "polling": 1000, "property": {}, "tags": {}},
        "devices": {DEV_ID: device()},
        "hmi": {"layout": {"start": VIEW_ID, "navigation": {"mode": "none"},
                           "header": {"title": "T-101 Rotterdam"},
                           "showdev": True, "theme": "dark"},
                "views": [view()]},
        # One realtime chart, three lines. ChartLine needs device NAME plus
        # tag id — the same pairing as a gauge binding, minus the ^~^ join.
        "charts": [{
            "id": "chart_t101", "name": "T-101 Trend",
            "lines": [
                {"id": tag_id("level"),   "name": tag_id("level"),
                 "device": DEV_NAME, "color": "#4a9eff", "yaxis": 1, "lineWidth": 2},
                {"id": tag_id("inflow"),  "name": tag_id("inflow"),
                 "device": DEV_NAME, "color": "#3fb950", "yaxis": 1, "lineWidth": 2},
                {"id": tag_id("outflow"), "name": tag_id("outflow"),
                 "device": DEV_NAME, "color": "#d29922", "yaxis": 1, "lineWidth": 2},
            ]}],
        # clientAccess is NOT optional, whatever project.demo.fuxap suggests by
        # omitting it. On every HMI load ScriptService.loadScriptApi runs:
        #
        #     const ui = this.projectService.getClientAccess()
        #     if (ui.scriptSystemFunctions.includes(ne.name)) ...
        #
        # With the key absent — or present as {} — scriptSystemFunctions is
        # undefined and .includes() throws. That kills the load pipeline before
        # a single gauge is bound. The SVG still draws, so it presents as a
        # binding problem rather than a crash, which is what made it expensive
        # to find. The model (client-access.ts) is one field, defaulting to [].
        "clientAccess": {"scriptSystemFunctions": []},
    }

if __name__ == "__main__":
    p = project()
    out = json.dumps(p)
    open("/tmp/fuxa-project.json", "w").write(out)
    print(f"project: {len(out)} bytes, {len(p['devices'][DEV_ID]['tags'])} tags, "
          f"{len(p['hmi']['views'][0]['items'])} bound items")
    def post(path, payload):
        req = urllib.request.Request(f"{FUXA}{path}", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return f"{r.status}"
        except Exception as e:
            body = getattr(e, "read", lambda: b"")()
            return f"FAILED {e} {body[:200].decode(errors='replace')}"

    # 1. Seed the whole project. This stores it but does NOT re-initialise the
    #    runtime, which is why a bulk POST alone leaves every gauge at zero.
    print("POST /api/project      ->", post("/api/project", p))

    # 2. Then push each part through /api/projectData. That route calls
    #    runtime.update(cmd, data) after saving — the step that actually
    #    rebuilds device subscriptions and rebinds the view. Command strings
    #    come from ProjectDataCmdType in project.ts.
    print("  cmd set-device       ->", post("/api/projectData",
          {"cmd": "set-device", "data": p["devices"][DEV_NAME]}))
    print("  cmd charts           ->", post("/api/projectData",
          {"cmd": "charts", "data": p["charts"]}))
    print("  cmd set-view         ->", post("/api/projectData",
          {"cmd": "set-view", "data": p["hmi"]["views"][0]}))
