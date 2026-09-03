"""
gen_points.py — PROD.

Regenerates _points_data.json straight from data.js's own stage dates (no date-shifting;
that's shift_dates.py's job and TEST-only). Run this any time wxPoints changes in data.js
(new GPX, a VP location correction, etc.) — fetch_weather.py always reads _points_data.json,
it never reads data.js directly, so a wxPoints edit that isn't followed by this script
silently never reaches the weather fetch.

Same idx-based key scheme as shift_dates.py's version — see index.html's
wxHourKeyForPoint() and the comment above it for why idx (not array position) is the key,
and why A/B route variants share one fetch point per VP label.
"""
import json

with open("data.js", encoding="utf-8") as f:
    raw = f.read()
prefix = "var RIDE="
d = json.loads(raw[len(prefix):].rstrip(";\n"))

anchor_hour = {0: 8, 1: 11, 2: 14, 3: 16}  # rough per-index snapshot hour, keyed by idx
points = []
for s in d["stages"]:
    for wx in s["wxPoints"]:
        if wx.get("tbd"):
            continue  # location not confirmed yet — never fetch weather for a guess
        idx = wx["idx"]
        points.append({
            "key": f"{s['num']}-{idx}",
            "lat": round(wx["lat"], 4),
            "lon": round(wx["lon"], 4),
            "ele": wx["ele"],
            "date": s["iso"],
            "hour": anchor_hour[idx],
        })

with open("_points_data.json", "w") as f:
    json.dump(points, f)

print(f"wrote _points_data.json: {len(points)} points")
for p in points:
    print(" ", p["key"], p["date"], p["hour"], p["lat"], p["lon"])
