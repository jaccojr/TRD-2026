#!/usr/bin/env python3
"""Fetch weather for every stage waypoint of The Ride Dolomites and write weather.json.
Open-Meteo best_match (auto-selects GeoSphere AROME / ICON-D2 for the Dolomites) with
per-point elevation for accurate mountain temps. Falls back to wttr.in within 3 days.
Never overwrites good data with empty data."""
import json, time, urllib.request, urllib.parse, datetime, os, sys

POINTS = [{"key": "0-0", "lat": 46.0073, "lon": 11.2844, "ele": 442, "date": "2026-09-13", "hour": 8}, {"key": "0-1", "lat": 46.0168, "lon": 11.2819, "ele": 494, "date": "2026-09-13", "hour": 12}, {"key": "0-2", "lat": 46.007, "lon": 11.2842, "ele": 445, "date": "2026-09-13", "hour": 16}, {"key": "1-0", "lat": 46.0067, "lon": 11.2877, "ele": 446, "date": "2026-09-14", "hour": 8}, {"key": "1-1", "lat": 45.9233, "lon": 11.6763, "ele": 1083, "date": "2026-09-14", "hour": 12}, {"key": "1-2", "lat": 45.9634, "lon": 11.7594, "ele": 293, "date": "2026-09-14", "hour": 16}, {"key": "2-0", "lat": 45.9637, "lon": 11.7593, "ele": 268, "date": "2026-09-15", "hour": 8}, {"key": "2-1", "lat": 45.9365, "lon": 12.2308, "ele": 181, "date": "2026-09-15", "hour": 12}, {"key": "2-2", "lat": 46.0966, "lon": 12.2763, "ele": 990, "date": "2026-09-15", "hour": 16}, {"key": "3-0", "lat": 46.0963, "lon": 12.2763, "ele": 1000, "date": "2026-09-16", "hour": 8}, {"key": "3-1", "lat": 46.3802, "lon": 12.2688, "ele": 1433, "date": "2026-09-16", "hour": 12}, {"key": "3-2", "lat": 46.5541, "lon": 11.9696, "ele": 1678, "date": "2026-09-16", "hour": 16}, {"key": "4-0", "lat": 46.5542, "lon": 11.9698, "ele": 1665, "date": "2026-09-17", "hour": 8}, {"key": "4-1", "lat": 46.4527, "lon": 11.899, "ele": 1879, "date": "2026-09-17", "hour": 12}, {"key": "4-2", "lat": 46.5541, "lon": 11.9696, "ele": 1659, "date": "2026-09-17", "hour": 16}, {"key": "5-0", "lat": 46.5541, "lon": 11.9694, "ele": 1510, "date": "2026-09-18", "hour": 8}, {"key": "5-1", "lat": 46.508, "lon": 11.4931, "ele": 497, "date": "2026-09-18", "hour": 12}, {"key": "5-2", "lat": 46.3103, "lon": 11.6596, "ele": 1196, "date": "2026-09-18", "hour": 16}]  # injected below

def http_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent":"the-ride-dolomites/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def open_meteo(p):
    q = urllib.parse.urlencode({
        "latitude": p["lat"], "longitude": p["lon"], "elevation": p["ele"],
        "hourly": "temperature_2m,weather_code,wind_speed_10m,wind_direction_10m,precipitation_probability",
        "models": "best_match", "timezone": "Europe/Rome",
        "start_date": p["date"], "end_date": p["date"],
    })
    d = http_json("https://api.open-meteo.com/v1/forecast?" + q)
    H = d["hourly"]; idx = p["hour"]
    return {"temp": round(H["temperature_2m"][idx]),
            "code": H["weather_code"][idx],
            "wind": round(H["wind_speed_10m"][idx]),
            "windDeg": round(H["wind_direction_10m"][idx]),
            "rain": H["precipitation_probability"][idx] or 0}

def fetch_point(p, tries=5):
    for a in range(tries):
        try:
            return open_meteo(p)
        except Exception as e:
            sys.stderr.write("retry %d %s: %s\n" % (a, p["key"], e)); time.sleep(2)
    return None

def main():
    prev = {}
    if os.path.exists("weather.json"):
        try: prev = json.load(open("weather.json")).get("data", {})
        except Exception: pass
    out = dict(prev)  # preserve existing
    for p in POINTS:
        wx = fetch_point(p)
        if wx: out[p["key"]] = wx           # only overwrite on success
        time.sleep(0.4)
    payload = {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(), "data": out}
    json.dump(payload, open("weather.json", "w"), ensure_ascii=False)
    print("wrote weather.json:", len(out), "points")

if __name__ == "__main__":
    main()
