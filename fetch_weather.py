import json, os, sys, time, datetime, urllib.request

with open(os.path.join(os.path.dirname(__file__), "_points_data.json")) as _f:
    POINTS = json.load(_f)

def open_meteo(p):
    url = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
           "&hourly=temperature_2m,weather_code,wind_speed_10m,wind_direction_10m,precipitation_probability"
           "&timezone=auto&start_date=%s&end_date=%s&models=best_match"
           % (p["lat"], p["lon"], p["date"], p["date"]))
    req = urllib.request.Request(url, headers={"User-Agent": "trd-weather-bot"})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read().decode())
    H = d["hourly"]
    times = H["time"]
    target = "%sT%02d:00" % (p["date"], p["hour"])
    idx = times.index(target) if target in times else p["hour"]
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
    out = dict(prev)  # preserve existing values; only overwrite on a successful fetch
    for p in POINTS:
        wx = fetch_point(p)
        if wx: out[p["key"]] = wx
        time.sleep(0.4)
    payload = {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(), "data": out}
    json.dump(payload, open("weather.json", "w"), ensure_ascii=False)
    print("wrote weather.json:", len(out), "points")

if __name__ == "__main__":
    main()
