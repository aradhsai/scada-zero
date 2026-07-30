"""Tag map for T-101. One entry per MQTT topic the Node-RED model publishes.

Keeping this in one place means the device definition and every screen binding
are generated from the same list — the screen cannot drift from the process,
which is the whole reason for generating the project rather than clicking it.
"""

BASE = "northwind/rotterdam/T101"

# FUXA keys its devices dictionary by NAME, not id, and a gauge references a
# tag as "<deviceName>^~^<tagId>". Neither fact is in the documentation — both
# came out of the shipped project.demo.fuxap. Keep the name free of spaces so
# the composite key stays easy to read.
DEV_NAME = "T101"

# (key, topic suffix, type, unit, digits, description)
TAGS = [
    ("level",      "level",            "number", "%",    1, "Tank level"),
    ("volume",     "volume",           "number", "m3",   1, "Tank volume"),
    ("inflow",     "inflow",           "number", "m3/h", 1, "Inlet flow"),
    ("outflow",    "outflow",          "number", "m3/h", 1, "Discharge flow"),
    ("totaliser",  "totaliser",        "number", "m3",   0, "Transferred total"),
    ("valvePos",   "valve/position",   "number", "%",    0, "XV-101 position"),
    ("valveCmd",   "valve/command",    "number", "%",    0, "XV-101 command"),
    ("pArun",      "pumpA/running",    "number", "",     0, "P-101A running"),
    ("pAspd",      "pumpA/speed",      "number", "%",    0, "P-101A speed"),
    ("pAhrs",      "pumpA/hours",      "number", "h",    1, "P-101A runtime"),
    ("pAflt",      "pumpA/fault",      "number", "",     0, "P-101A fault"),
    ("pBrun",      "pumpB/running",    "number", "",     0, "P-101B running"),
    ("pBspd",      "pumpB/speed",      "number", "%",    0, "P-101B speed"),
    ("pBhrs",      "pumpB/hours",      "number", "h",    1, "P-101B runtime"),
    ("pBflt",      "pumpB/fault",      "number", "",     0, "P-101B fault"),
    ("duty",       "duty",             "string", "",     0, "Duty pump"),
    ("mode",       "mode",             "string", "",     0, "Control mode"),
    ("spStart",    "setpoint/start",   "number", "%",    0, "Pump start setpoint"),
    ("spStop",     "setpoint/stop",    "number", "%",    0, "Pump stop setpoint"),
    ("spLL",       "setpoint/LL",      "number", "%",    0, "Low low setpoint"),
    ("spHH",       "setpoint/HH",      "number", "%",    0, "High high setpoint"),
    ("aLL",        "alarm/LL",         "number", "",     0, "LL alarm"),
    ("aL",         "alarm/L",          "number", "",     0, "L alarm"),
    ("aH",         "alarm/H",          "number", "",     0, "H alarm"),
    ("aHH",        "alarm/HH",         "number", "",     0, "HH alarm"),
    ("aAny",       "alarm/active",     "number", "",     0, "Any alarm active"),
]

def tag_id(key):
    return f"t101_{key}"

def vref(key):
    """The three fields FUXA needs to resolve a tag from a gauge."""
    # variableId must equal the id the SERVER puts on the wire, because
    # hmi.service.ts keys its variable map on that value verbatim:
    #     const originalId = message.values[idx].id
    #     updateVariable(originalId, ...)
    # Captured frame: 42["device-values",{"id":"T101","values":[
    #   {"id":"t101_level","value":33.8}, ...]}]
    # i.e. the bare tag id, NOT deviceName^~^tagId. The ^~^ form in
    # project.demo.fuxap is what the editor writes, but it is not what the
    # runtime matches against for an MQTT device.
    return {"variableId": tag_id(key),
            "variableSrc": DEV_NAME,
            "variable": tag_id(key)}
