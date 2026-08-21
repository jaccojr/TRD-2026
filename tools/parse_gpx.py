import sys, re, math, json
import xml.etree.ElementTree as ET

NS = {'g': 'http://www.topografix.com/GPX/1/1'}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    return 2*R*math.asin(math.sqrt(a))

def parse(fn):
    tree = ET.parse(fn)
    root = tree.getroot()
    trkpts = []
    for trkpt in root.findall('.//g:trkpt', NS):
        lat = float(trkpt.get('lat')); lon = float(trkpt.get('lon'))
        eleEl = trkpt.find('g:ele', NS)
        ele = float(eleEl.text) if eleEl is not None else None
        trkpts.append((lat, lon, ele))

    wpts = []
    for wpt in root.findall('.//g:wpt', NS):
        lat = float(wpt.get('lat')); lon = float(wpt.get('lon'))
        nameEl = wpt.find('g:name', NS)
        descEl = wpt.find('g:desc', NS)
        symEl = wpt.find('g:sym', NS)
        typeEl = wpt.find('g:type', NS)
        eleEl = wpt.find('g:ele', NS)
        wpts.append({
            'lat': lat, 'lon': lon,
            'name': nameEl.text if nameEl is not None else None,
            'desc': descEl.text if descEl is not None else None,
            'sym': symEl.text if symEl is not None else None,
            'type': typeEl.text if typeEl is not None else None,
            'ele': float(eleEl.text) if eleEl is not None and eleEl.text else None,
        })

    # cumulative distance
    dist = 0.0
    dists = [0.0]
    for i in range(1, len(trkpts)):
        dist += haversine(trkpts[i-1][0], trkpts[i-1][1], trkpts[i][0], trkpts[i][1])
        dists.append(dist)

    # elevation gain/loss with a simple smoothing threshold to avoid GPS noise
    elevs = [t[2] for t in trkpts if t[2] is not None]
    gain = loss = 0.0
    if elevs:
        smoothed = []
        window = 5
        for i in range(len(elevs)):
            lo = max(0, i-window); hi = min(len(elevs), i+window+1)
            smoothed.append(sum(elevs[lo:hi]) / (hi-lo))
        for i in range(1, len(smoothed)):
            d = smoothed[i] - smoothed[i-1]
            if d > 0: gain += d
            else: loss += -d

    return {
        'file': fn,
        'n_trkpts': len(trkpts),
        'trkpts': trkpts,
        'dists': dists,
        'total_dist_km': dist/1000.0,
        'gain_m': gain,
        'loss_m': loss,
        'max_ele': max(elevs) if elevs else None,
        'min_ele': min(elevs) if elevs else None,
        'start': trkpts[0] if trkpts else None,
        'end': trkpts[-1] if trkpts else None,
        'wpts': wpts,
    }

if __name__ == '__main__':
    fn = sys.argv[1]
    r = parse(fn)
    print(json.dumps({
        'file': r['file'], 'n_trkpts': r['n_trkpts'],
        'total_dist_km': round(r['total_dist_km'],1),
        'gain_m': round(r['gain_m']), 'loss_m': round(r['loss_m']),
        'max_ele': round(r['max_ele']) if r['max_ele'] else None,
        'min_ele': round(r['min_ele']) if r['min_ele'] else None,
        'start': r['start'], 'end': r['end'],
        'n_wpts': len(r['wpts']),
        'wpts': r['wpts'],
    }, indent=1, ensure_ascii=False))
