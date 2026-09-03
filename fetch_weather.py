import json, os, sys, time, datetime, urllib.request, urllib.error

with open(os.path.join(os.path.dirname(__file__), "_points_data.json")) as _f:
    POINTS = json.load(_f)

# Must match RIDER_RANGE_MIN/MAX in index.html (7*60 .. 18*60) — the rider time-slider
# never renders outside this window, so this is the full range we need hourly data for.
RIDER_HOUR_LO = 7
RIDER_HOUR_HI = 18

def hour_slice(H, idx):
    return {"temp": round(H["temperature_2m"][idx]),
            "code": H["weather_code"][idx],
            "wind": round(H["wind_speed_10m"][idx]),
            "windDeg": round(H["wind_direction_10m"][idx]),
            "rain": H["precipitation_probability"][idx] or 0}

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
    result = hour_slice(H, idx)
    # Full hourly breakdown across the rider-slider window — same response, just kept
    # instead of discarded. Missing hours (e.g. outside Open-Meteo's returned day) are
    # simply omitted rather than guessed.
    hourly = {}
    for hr in range(RIDER_HOUR_LO, RIDER_HOUR_HI + 1):
        t = "%sT%02d:00" % (p["date"], hr)
        if t in times:
            hourly[str(hr)] = hour_slice(H, times.index(t))
    result["hourly"] = hourly
    return result

def fetch_point(p, tries=5):
    for a in range(tries):
        try:
            return open_meteo(p)
        except urllib.error.HTTPError as e:
            if e.code == 400:
                # date is outside Open-Meteo's forecast horizon — this won't change on retry
                sys.stderr.write("skip %s: HTTP 400 (date out of forecast range)\n" % p["key"])
                return None
            sys.stderr.write("retry %d %s: HTTP %d\n" % (a, p["key"], e.code)); time.sleep(2)
        except Exception as e:
            sys.stderr.write("retry %d %s: %s\n" % (a, p["key"], e)); time.sleep(2)
    return None

def main():
    prev = {}
    if os.path.exists("weather.json"):
        try: prev = json.load(open("weather.json")).get("data", {})
        except Exception: pass
    # Carry forward only keys that are still in the current point list. This preserves the
    # failed-fetch protection intact — a current point whose fetch fails this run keeps its
    # previous value, because its key survives this filter — while dropping orphans left
    # behind by retired point schemes (e.g. the old 3-point "0-2" finish index and the old
    # A/B "2-1b"/"5-1b" midpoints). Without this, weather.json only ever grew: nothing
    # removed a key just because it stopped being generated.
    current_keys = {p["key"] for p in POINTS}
    dropped = sorted(k for k in prev if k not in current_keys)
    out = {k: v for k, v in prev.items() if k in current_keys}
    if dropped:
        print("dropped %d stale key(s): %s" % (len(dropped), ", ".join(dropped)))
    failed = []
    for p in POINTS:
        wx = fetch_point(p)
        if wx: out[p["key"]] = wx
        else: failed.append(p["key"])
        time.sleep(0.4)
    payload = {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(), "data": out}
    json.dump(payload, open("weather.json", "w"), ensure_ascii=False)
    print("wrote weather.json:", len(out), "points")
    if failed:
        # Fail the job *after* writing whatever succeeded, so the run shows red in the Actions
        # tab instead of looking identical to a clean run -- previously nothing signalled a
        # failure beyond stderr lines nobody was watching, so even a 100%-failed run stayed
        # green. A failed point here still keeps its carried-forward value in weather.json
        # above (or is simply absent if it has never once succeeded) -- this exit code only
        # affects whether the run gets flagged, never whether data gets written.
        sys.stderr.write("FAILED to fetch %d/%d point(s): %s\n" % (len(failed), len(POINTS), ", ".join(failed)))
        sys.exit(1)

if __name__ == "__main__":
    main()
