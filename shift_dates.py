"""
shift_dates.py — TEST REPO ONLY.

Keeps The Ride Dolomites TEST build permanently anchored so "today" always
equals "the day before Proloog" (the 12/9-equivalent state), no matter what
the real calendar date is. Run this before fetch_weather.py in the workflow.

Why: a one-time static date shift (e.g. "September -> July") goes stale the
moment real time moves past the shifted window — weather stops being
fetchable (outside Open-Meteo's ~16-day horizon) and the Today-tab state
stops being reproducible. This script recomputes Proloog as tomorrow
(UTC date + 1) every time it runs, so both problems are solved permanently:
weather dates are always 1-6 days out (always fetchable), and "today" is
always the fixed, testable "day before the tour starts" state.

Only ever touches the TEST repo — never run this against the real data.js.
"""
import json
import re
import datetime

DUTCH_WEEKDAY = ["ma", "di", "wo", "do", "vr", "za", "zo"]  # Python Monday=0

def dutch_date_label(d):
    return f"{DUTCH_WEEKDAY[d.weekday()]} {d.day}/{d.month}"

def shift():
    today = datetime.datetime.now(datetime.timezone.utc).date()
    proloog = today + datetime.timedelta(days=1)  # Proloog is always "tomorrow"

    with open("data.js", encoding="utf-8") as f:
        raw = f.read()
    prefix = "var RIDE="
    d = json.loads(raw[len(prefix):].rstrip(";\n"))

    # --- stages: Proloog+0 through Proloog+5 ---
    stage_dates = [proloog + datetime.timedelta(days=i) for i in range(len(d["stages"]))]
    for s, dt in zip(d["stages"], stage_dates):
        s["iso"] = dt.isoformat()
        s["date"] = dutch_date_label(dt)

    # --- campSchedule: Proloog-2 through Proloog+5, matching the existing
    #     [-2,-1,0,0,1,1,2,2,3,3,4,4,5,5] relative-offset pattern exactly ---
    offsets = [-2, -1, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
    old_isos = [row["iso"] for row in d["event"]["campSchedule"]]
    new_isos = [(proloog + datetime.timedelta(days=o)).isoformat() for o in offsets[:len(old_isos)]]

    # build old-day/month -> new-day/month map for embedded "(12/7)"-style text substitution
    old_dates = [datetime.date.fromisoformat(iso) for iso in old_isos]
    date_map = {f"{od.day}/{od.month}": f"{datetime.date.fromisoformat(ni).day}/{datetime.date.fromisoformat(ni).month}"
                for od, ni in zip(old_dates, new_isos)}

    for row, new_iso in zip(d["event"]["campSchedule"], new_isos):
        row["iso"] = new_iso
        for k in ("diner", "ontbijt", "start"):
            if row.get(k):
                pattern = re.compile(r"\((" + "|".join(re.escape(k2) for k2 in date_map) + r")\)")
                row[k] = pattern.sub(lambda m: "(" + date_map[m.group(1)] + ")", row[k])

    with open("data.js", "w", encoding="utf-8") as f:
        f.write(prefix + json.dumps(d, ensure_ascii=False) + ";")

    # --- _points_data.json: regenerate from the freshly-shifted stage wxPoints.
    #     The key index comes from each point's own "idx" field in data.js — the single
    #     source of truth, shared with index.html's wxHourKeyForPoint(). Previously this
    #     script and index.html each kept their own Start/VP1/VP2/Finish -> 0/1/2/3 table,
    #     so adding a point would have needed both edited in lockstep (in two languages)
    #     or the app would silently look up keys this script never wrote.
    #
    #     idx is deliberately NOT the array position: Etappe 5B has no VP1, so its VP2 sits
    #     at position 1 while still needing key index 2.
    #
    #     No separate A/B fetch points are generated: VP1/VP2 are the same physical
    #     location in both variants for every stage that has them (confirmed directly
    #     against the GPX — coordinates match to the decimal), so one fetch point per
    #     label is correct and sufficient; there is nothing for a "-b" key to represent.
    points = []
    anchor_hour = {0: 8, 1: 11, 2: 14, 3: 16}  # rough per-index snapshot hour, keyed by idx
    for s in d["stages"]:
        for wx in s["wxPoints"]:
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

    print(f"Shifted: Proloog now {proloog.isoformat()} (today={today.isoformat()})")
    for s in d["stages"]:
        print(f"  {s['num']} {s['it']}: {s['iso']}")

if __name__ == "__main__":
    shift()
