import json, math, sys
from parse_gpx import parse, haversine

def nearest_idx(trkpts, lat, lon):
    best_i, best_d = 0, float('inf')
    for i, (tlat, tlon, _) in enumerate(trkpts):
        d = (tlat-lat)**2 + (tlon-lon)**2  # cheap proxy, fine at this scale for nearest-point
        if d < best_d:
            best_d, best_i = d, i
    return best_i

def categorize(w):
    name = (w['name'] or '').strip()
    lname = name.lower()
    sym = (w['sym'] or '')
    if sym == 'Drinking Water' or 'drinkfontein' in lname or 'fountain' in lname:
        return 'water'
    if lname.replace(' ', '').startswith('vp') or lname.startswith('vp '):
        return 'vp'
    if lname.startswith('let op'):
        return 'warning'
    if 'challenge' in lname:
        return 'challenge'
    if 'placeholder' in lname:
        return 'placeholder'
    if any(k in lname for k in ['pass', 'passo', 'klim', 'col']):
        return 'climb-marker'
    return 'other'

def main(fn):
    r = parse(fn)
    trkpts, dists = r['trkpts'], r['dists']
    out = []
    for w in r['wpts']:
        idx = nearest_idx(trkpts, w['lat'], w['lon'])
        km = dists[idx] / 1000.0
        ele = trkpts[idx][2]
        out.append({
            'km': round(km, 1),
            'lat': w['lat'], 'lon': w['lon'],
            'ele': round(ele) if ele else w['ele'],
            'name': w['name'], 'desc': w['desc'],
            'cat': categorize(w),
        })
    out.sort(key=lambda x: x['km'])
    return out

if __name__ == '__main__':
    result = main(sys.argv[1])
    print(json.dumps(result, indent=1, ensure_ascii=False))
