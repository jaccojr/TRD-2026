"""
Rebuilds the TRD-2026 gradient -> speed curve from Jacco's own real ride GPX files.

Method (verified this session against the live app):
  1. Parse each workout GPX: lat/lon/ele/time per point.
  2. Compute cumulative distance (haversine) and per-point speed (real elapsed time,
     not assumed constant sampling).
  3. Detect stops: sustained low-speed intervals (<2.5 km/h, >30s), merging intervals
     that are close together in time/distance (a single stop can otherwise appear as
     two intervals split by one noisy GPS point above the threshold).
  4. Walk the ride in 150m rolling windows. For each window, compute its own real
     gradient and real speed, excluding any window that overlaps a detected stop.
     Gradient is NEVER averaged across a larger span first -- the speed-gradient
     relationship is non-linear, so averaging gradient before computing speed
     understates time on any segment with mixed pitches (verified: this specific
     mistake understated stage times by 4-21 minutes when first caught).
  5. Pool all windows from all rides together. Bucket by 1% gradient resolution.
     Speed per bucket = total_distance / total_time across all windows in that
     bucket (distance-weighted, not a simple average of per-window speeds).

Output: gradient_speed_curve.json, a plain {"-16": 12.3, "-15": 14.1, ...} map from
integer gradient bucket (percent, can be negative for descents) to real speed in km/h.
Also prints the same table for a readable copy.

Apply it exactly like the live app does: for a new stage's GPX, walk it in the same
150m windows, look up each window's own gradient in this table (nearest bucket if a
window's grade falls outside the range this data covers), multiply by FIELD_SCALE,
and sum -- never average gradient across a whole segment first.
"""
import xml.etree.ElementTree as ET
import math, json
from datetime import datetime

NS = {'g': 'http://www.topografix.com/GPX/1/1'}
WORKOUT_FILES = [
    'The_Ride_2026_day_2.gpx',
    'The_Ride_2026_day_3.gpx',
    'The_Ride_2026_day_8_Finished_.gpx',
]
STOP_SPEED_THRESH = 2.5   # km/h
STOP_MIN_DURATION = 30    # seconds
STOP_MERGE_GAP_KM = 0.3
STOP_MERGE_GAP_IDX = 300
WINDOW_KM = 0.15
BUCKET_RANGE = range(-16, 16)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))


def parse_iso(t):
    return datetime.fromisoformat(t.replace('Z', '+00:00'))


def parse_workout(path):
    tree = ET.parse(path)
    pts = []
    for trkpt in tree.findall('.//g:trkpt', NS):
        lat = float(trkpt.get('lat')); lon = float(trkpt.get('lon'))
        ele_el = trkpt.find('g:ele', NS)
        time_el = trkpt.find('g:time', NS)
        if ele_el is None or time_el is None:
            continue
        pts.append({'lat': lat, 'lon': lon, 'ele': float(ele_el.text), 't': parse_iso(time_el.text)})
    cum = 0.0
    pts[0].update({'km': 0.0, 'dt': 0, 'speed': 0})
    for i in range(1, len(pts)):
        d = haversine_km(pts[i-1]['lat'], pts[i-1]['lon'], pts[i]['lat'], pts[i]['lon'])
        cum += d
        dt = (pts[i]['t'] - pts[i-1]['t']).total_seconds()
        pts[i].update({'km': cum, 'dt': dt, 'speed': (d/(dt/3600)) if dt > 0 else 0})
    return pts


def detect_stops(pts):
    stops = []
    in_stop = False
    si = None
    for i in range(1, len(pts)):
        slow = pts[i]['speed'] < STOP_SPEED_THRESH
        if slow and not in_stop:
            in_stop = True; si = i
        elif not slow and in_stop:
            in_stop = False
            dur = sum(pts[j]['dt'] for j in range(si, i))
            if dur > STOP_MIN_DURATION:
                stops.append({'start_i': si, 'end_i': i, 'km': pts[si]['km']})
    if in_stop:
        dur = sum(pts[j]['dt'] for j in range(si, len(pts)))
        if dur > STOP_MIN_DURATION:
            stops.append({'start_i': si, 'end_i': len(pts)-1, 'km': pts[si]['km']})
    merged = []
    for s in stops:
        if merged and (s['km'] - merged[-1]['km']) < STOP_MERGE_GAP_KM and s['start_i'] - merged[-1]['end_i'] < STOP_MERGE_GAP_IDX:
            merged[-1]['end_i'] = s['end_i']
        else:
            merged.append(dict(s))
    stopped_idx = set()
    for s in merged:
        for i in range(s['start_i'], s['end_i']+1):
            stopped_idx.add(i)
    return stopped_idx


def extract_windows(pts, stopped_idx):
    out = []
    n = len(pts)
    si = 0
    while si < n-1:
        ei = si
        km0 = pts[si]['km']
        while ei < n-1 and pts[ei]['km'] - km0 < WINDOW_KM:
            ei += 1
        if ei <= si:
            si += 1; continue
        d = pts[ei]['km'] - pts[si]['km']
        ele = pts[ei]['ele'] - pts[si]['ele']
        tsec = sum(pts[j]['dt'] for j in range(si+1, ei+1) if j not in stopped_idx)
        has_stop = any(j in stopped_idx for j in range(si, ei+1))
        if d > 0.05 and tsec > 0 and not has_stop:
            grade = (ele / (d*1000)) * 100
            speed = d / (tsec/3600)
            out.append({'grade': grade, 'speed': speed, 'dist': d})
        si = ei
    return out


def build_curve(windows):
    curve = {}
    for b in BUCKET_RANGE:
        sel = [r for r in windows if b <= r['grade'] < b+1]
        if sel:
            dist = sum(r['dist'] for r in sel)
            time_h = sum(r['dist']/r['speed'] for r in sel)
            curve[b] = {'speed_kmh': round(dist/time_h, 2), 'km': round(dist, 1), 'n': len(sel)}
    return curve


def main():
    all_windows = []
    for path in WORKOUT_FILES:
        pts = parse_workout(path)
        stopped = detect_stops(pts)
        windows = extract_windows(pts, stopped)
        print(f'{path}: {len(pts)} points, {len(windows)} clean windows')
        all_windows.extend(windows)

    print(f'\nTotal pooled windows: {len(all_windows)}')
    curve = build_curve(all_windows)

    print(f'\n{"grade":>8} {"speed":>7} {"km":>7} {"n":>5}')
    for b in sorted(curve):
        c = curve[b]
        print(f'{b:>3}..{b+1:<3} {c["speed_kmh"]:>7.2f} {c["km"]:>7.1f} {c["n"]:>5}')

    # plain lookup table for direct reuse: {gradient_bucket: speed_kmh}
    lookup = {str(b): curve[b]['speed_kmh'] for b in curve}
    with open('gradient_speed_curve.json', 'w') as f:
        json.dump(lookup, f, indent=1)
    print('\nSaved gradient_speed_curve.json')


if __name__ == '__main__':
    main()
