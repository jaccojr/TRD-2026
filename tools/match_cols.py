import json, math
from parse_gpx import parse, haversine

KNOWN_COLS = json.loads('''
[
{"name": "Pian dei Pradi", "lat": 45.978387, "lon": 11.236387, "ele": 863, "profile": "climb-piandeipradi.png", "desc": "CAT 2 · 6,4 km, 5,6%"},
{"name": "Passo del Compet", "lat": 46.039335, "lon": 11.299844, "ele": 1373, "profile": "climb-compet.png", "desc": "CAT 1 · 10,2 km, 8,2%"},
{"name": "Passo della Forcella", "lat": 46.070998, "lon": 11.592046, "ele": 912, "profile": "climb-forcella.png", "desc": "CAT 2 · 12,3 km, 4,5%"},
{"name": "Passo Brocon", "lat": 46.118614, "lon": 11.688537, "ele": 1608, "profile": "climb-brocon.png", "desc": "CAT 1 · 18,7 km, 4,4%"},
{"name": "Passo Gobbera", "lat": 46.147616, "lon": 11.758362, "ele": 982, "profile": "climb-gobbera.png", "desc": "CAT 3 · 7,0 km, 3,8%"},
{"name": "Passo Rolle", "lat": 46.296237, "lon": 11.788217, "ele": 1969, "profile": "climb-rolle-predazzo.png", "desc": "CAT 1 · 21,4 km, 5,8%"},
{"name": "Passo Sella", "lat": 46.50807, "lon": 11.767318, "ele": 2220, "profile": "climb-sella.png", "desc": "CAT HC · 14,6 km, 5,5%"},
{"name": "Passo Gardena", "lat": 46.549793, "lon": 11.808457, "ele": 2109, "profile": "climb-gardena.png", "desc": "CAT 3 · 5,7 km, 4,3%"},
{"name": "Passo Valparola / Passo di Falzarego", "lat": 46.525018, "lon": 11.997521, "ele": 2183, "profile": "climb-valparola.png", "desc": "CAT 1 · 13,8 km, 5,7%"},
{"name": "Passo Giau", "lat": 46.482649, "lon": 12.053127, "ele": 2221, "profile": "climb-giau.png", "desc": "CAT HC · 9,2 km, 7,9%"},
{"name": "Passo di Fedaia", "lat": 46.454399, "lon": 11.886535, "ele": 2052, "profile": "climb-fedaia.png", "desc": "CAT HC · 14,0 km, 7,5%"},
{"name": "Passo Pordoi", "lat": 46.48696, "lon": 11.81357, "ele": 2231, "profile": "climb-pordoi.png", "desc": "CAT 1 · 15,6 km, 5,2%"},
{"name": "San Tomaso Agordino", "lat": 46.382056, "lon": 11.974559, "ele": 1082, "profile": "climb-santomaso.png", "desc": "CAT 3 · 2,8 km, 9,5%"},
{"name": "Passo San Pellegrino", "lat": 46.378357, "lon": 11.79172, "ele": 1915, "profile": "climb-sanpellegrino.png", "desc": "CAT HC · 18,2 km, 6,2%"},
{"name": "Passo Valles", "lat": 46.3387, "lon": 11.800517, "ele": 2032, "profile": "climb-valles.png", "desc": "CAT 2 · 23,6 km, 2,9%"},
{"name": "Passo Cereda", "lat": 46.1927, "lon": 11.9039, "ele": 1366, "profile": "climb-cereda.png", "desc": "CAT 1 · 25,0 km, 3,7%"},
{"name": "Passo Lavazè", "lat": 46.356556, "lon": 11.494963, "ele": 1812, "profile": "climb-lavaze.png", "desc": "CAT 1 · 14,5 km, 6,0%"},
{"name": "Passo Manghen", "lat": 46.173427, "lon": 11.441027, "ele": 2023, "profile": "climb-manghen.png", "desc": "CAT HC · 16,2 km, 7,5%"}
]
''')

def match(fn, threshold_m=600):
    r = parse(fn)
    trkpts, dists = r['trkpts'], r['dists']
    out = []
    for col in KNOWN_COLS:
        best_i, best_d = 0, float('inf')
        for i, (lat, lon, _) in enumerate(trkpts):
            d = haversine(lat, lon, col['lat'], col['lon'])
            if d < best_d:
                best_d, best_i = d, i
        if best_d <= threshold_m:
            out.append({
                'name': col['name'], 'profile': col['profile'], 'desc': col['desc'],
                'km': round(dists[best_i]/1000.0, 1),
                'ele_here': round(trkpts[best_i][2]) if trkpts[best_i][2] else None,
                'ele_catalog': col['ele'],
                'offset_m': round(best_d),
            })
    out.sort(key=lambda x: x['km'])
    return out

if __name__ == '__main__':
    import sys
    files = {
        'proloog': 'raw-proloog.gpx', 'etappe1': 'raw-etappe1.gpx', 'etappe2': 'raw-etappe2.gpx',
        'etappe3': 'raw-etappe3.gpx', 'etappe4': 'raw-etappe4.gpx', 'etappe4-afgekort': 'raw-etappe4-afgekort.gpx',
        'etappe5': 'raw-etappe5.gpx',
    }
    allout = {}
    for name, fn in files.items():
        m = match(fn)
        allout[name] = m
        print(f"=== {name} ===")
        for c in m:
            print(f"  km={c['km']:6.1f}  {c['name']:38s} offset={c['offset_m']:4d}m  ele_here={c['ele_here']}  ele_catalog={c['ele_catalog']}  -> {c['profile']}")
        print()
    json.dump(allout, open('col_matches.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
