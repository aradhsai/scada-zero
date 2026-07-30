# scada-zero

A complete, working SCADA stack — HMI, historian, protocol layer and a live
process — that costs nothing to license and runs on one small machine.

```
Node-RED  ──MQTT──▶  Mosquitto  ──MQTT──▶  FUXA
 process model        broker              HMI + historian
```

Everything here is MIT or EPL. No licence server, no seat count, no tag limit,
nothing that expires.

| | | |
|---|---|---|
| [FUXA](https://github.com/frangoteam/FUXA) | SCADA / HMI, web-based | MIT |
| [Node-RED](https://nodered.org) | process simulation and integration | Apache 2.0 |
| [Mosquitto](https://mosquitto.org) | MQTT broker | EPL / EDL |

## What it runs

A tank transfer system at a fictional terminal: one tank, a modulating inlet
valve, two pumps in duty/standby with rotation on every start, level alarms and
a totaliser.

The process is not a sine wave. Level is integrated from a mass balance,

```
dV/dt = Qin - Qout
```

with `dt` taken from the clock rather than assumed, valve travel rate-limited to
12 %/s, pump speed ramps, and runtime hours accumulating per pump. Time is
compressed 20x so a full duty cycle completes in about three minutes; the
equations are untouched and every figure stays dimensionally correct.

## Run it

```bash
git clone https://github.com/aradhsai/scada-zero
cd scada-zero
docker compose up -d
```

| Service | URL |
|---|---|
| FUXA | http://localhost:1881 |
| Node-RED | http://localhost:1880 |
| Mosquitto | localhost:1883 (and 9001 for websockets) |

Then build the HMI:

```bash
cd generator && python3 build_project.py
```

Open FUXA and the mimic is there, bound to live data.

> Ports bind to `127.0.0.1` only. Reach it over a VPN or a tunnel rather than
> publishing it. The broker allows anonymous connections, which is fine for a
> lab on a loopback interface and is not fine anywhere else.

## The HMI is generated, not drawn

`generator/` builds the entire FUXA project — device, tags, the SVG mimic and
every binding — and posts it over the API. Editing `tags.py` or `screen.py` and
re-running rebuilds it identically.

```
generator/
  tags.py            one entry per MQTT topic; device and screen both read this
  screen.py          the P&ID as code — pipes, ISA symbols, bindings
  build_project.py   assembles the project and posts it
```

The point: a screen that is regenerated from a definition cannot drift from the
process it draws.

## Notes on FUXA's project format

Six things that cost time and are not in the documentation. All were found by
reading the shipped models, the built client bundle, the server-side MQTT
driver, and the example project inside the image.

1. **A gauge's `variableId` must equal the tag id the server puts on the wire.**
   The client keys its variable map on that value verbatim
   (`const originalId = message.values[idx].id`). For an MQTT device the frame
   carries the bare tag id, so `variableId` is `t101_level` — *not*
   `deviceName^~^tagId`. The `^~^` form is what the editor writes and copying it
   silently binds nothing.
2. **`clientAccess.scriptSystemFunctions` is mandatory**, even though the bundled
   example project omits `clientAccess` entirely. `ScriptService.loadScriptApi`
   dereferences it on every HMI load; if it is missing the load aborts before any
   gauge binds — and the SVG still draws, so it looks like a binding fault.
3. **`settings.broadcastAll` defaults to `false`**, so the server only pushes tags
   a client has explicitly subscribed to.
4. **Bound elements need a `type="svg-ext-..."` attribute on a `<g>` wrapper.** A
   bare `<text id=...>` never binds. HTML gauges need
   `<g type="svg-ext-html_chart"><rect/><foreignObject id="H-<itemId>"/></g>`.
5. **The `devices` dictionary is keyed by device name**, not id. A tag's `address`
   is the MQTT topic; raw scalar payloads bind directly, and only `type: "json"`
   triggers payload parsing via `memaddress`.
6. **`POST /api/project` stores without re-initialising the runtime.** Follow it
   with `POST /api/projectData` using `{cmd, data}` for `set-device`, `charts`
   and `set-view` — that path calls `runtime.update()`.

## History

FUXA logs to SQLite per device in `server/_db/`:

- `daq-map_<device>.db` — `data(mapid, id, name, type)`, an integer per tag
- `daq-data_<device>_<stamp>.db` — `data(dt, id, value)`, keyed by that integer

Files roll every `daqTokenizer` hours and archive. InfluxDB, QuestDB and TDengine
backends ship in `runtime/storage/` if SQLite is not enough.

`currentTagReadings.db` only holds tags marked `restored` — it is not a
live-value view, which is misleading while debugging.

## Licence

MIT. See [LICENSE](LICENSE).
