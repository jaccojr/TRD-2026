"""
Applies the real TRD-2026 gradient->speed curve (gradient_speed_curve.json, Jacco's own
pace) to the new stage GPX files to rebuild segmentComposition per stage — same 150m
rolling-window method as rebuild_curve.py used to build the curve itself, just walking
route GPX (lat/lon/ele only, no time) instead of a timed workout GPX: look up each
window's own real gradient in the curve (nearest available bucket), derive speed, sum
distance/speed into minutes, and bucket those minutes into whichever Start/VP1/VP2/Finish
segment the window falls in. FIELD_SCALE is NOT applied here — baseMin stays at Jacco's
own pace, exactly like the existing Etappe 1 data (156.62/164.27/95.09) does; the live
app's segmentRidingMinutes() divides by FIELD_SCALE at render time.
"""
import json, math, os
import xml.etree.ElementTree as ET

NS = {'g': 'http://www.topografix.com/GPX/1/1'}
WINDOW_KM = 0.15

# Resolved against this script's own folder, not the caller's cwd -- see the matching
# comment in rebuild_curve.py (2026-09-03 tools/ tidy-up).
CURVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gradient_speed_curve.json')
with open(CURVE_PATH) as f:
    CURVE = {int(k): v for k, v in json.load(f).items()}
CURVE_MIN, CURVE_MAX = min(CURVE), max(CURVE)

def speed_for_grade(g):
    b = math.floor(g)
    b = max(CURVE_MIN, min(CURVE_MAX, b))
    while b not in CURVE and b < CURVE_MAX:
        b += 1
    while b not in CURVE and b > CURVE_MIN:
        b -= 1
    return CURVE[b]

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def parse_route(fn):
    tree = ET.parse(fn)
    pts = []
    cum = 0.0
    prev = None
    for trkpt in tree.findall('.//g:trkpt', NS):
        lat = float(trkpt.get('lat')); lon = float(trkpt.get('lon'))
        ele_el = trkpt.find('g:ele', NS)
        ele = float(ele_el.text) if ele_el is not None else None
        if prev is not None:
            cum += haversine_km(prev[0], prev[1], lat, lon)
        pts.append({'lat': lat, 'lon': lon, 'ele': ele, 'km': cum})
        prev = (lat, lon)
    return pts

def extract_windows(pts):
    out = []
    n = len(pts)
    si = 0
    while si < n - 1:
        ei = si
        km0 = pts[si]['km']
        while ei < n - 1 and pts[ei]['km'] - km0 < WINDOW_KM:
            ei += 1
        if ei <= si:
            si += 1; continue
        d = pts[ei]['km'] - pts[si]['km']
        ele = (pts[ei]['ele'] - pts[si]['ele']) if (pts[ei]['ele'] is not None and pts[si]['ele'] is not None) else 0
        if d > 0.02:
            grade = (ele / (d * 1000)) * 100
            speed = speed_for_grade(grade)
            time_h = d / speed
            out.append({'km_mid': (pts[si]['km'] + pts[ei]['km']) / 2, 'dist': d, 'time_h': time_h})
        si = ei
    return out

def build_segments(fn, boundaries):
    """boundaries: list of (label, km) in route order, e.g. [('Start',0),('VP1',50.1),('VP2',92.5),('Finish',148.2)]"""
    pts = parse_route(fn)
    windows = extract_windows(pts)
    segs = []
    for i in range(len(boundaries) - 1):
        lo_label, lo_km = boundaries[i]
        hi_label, hi_km = boundaries[i+1]
        sel = [w for w in windows if lo_km <= w['km_mid'] < hi_km] if i < len(boundaries)-2 else [w for w in windows if w['km_mid'] >= lo_km]
        dist = sum(w['dist'] for w in sel)
        time_h = sum(w['time_h'] for w in sel)
        segs.append({'from': lo_label, 'to': hi_label, 'km': round(dist, 2), 'baseMin': round(time_h * 60, 2)})
    return segs

if __name__ == '__main__':
    # sanity check: rebuild Etappe1's OLD segmentComposition from the OLD gpx-etappe1.gpx
    # (still in test-repo) to see how close this reproduces 156.62/164.27/95.09
    old_bounds = [('Start', 0), ('VP1', 50.1), ('VP2', 106.2), ('Finish', 151.3)]
    segs = build_segments('/home/claude/test-repo/gpx-etappe1.gpx', old_bounds)
    print("Reproduction check vs OLD Etappe1 data (expect ~156.62 / 164.27 / 95.09):")
    for s in segs:
        print(" ", s)
