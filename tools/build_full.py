import json, math
import xml.etree.ElementTree as ET
from parse_gpx import parse as parse_full  # trkpts w/ ele, dists, wpts
from analyze_pois import main as analyze_pois
from compute_segments import build_segments, parse_route as parse_route_noEle_ok
from match_cols import match as match_cols, KNOWN_COLS

STAGES = [
    {'key': '0', 'num': 0, 'it': 'Proloog', 'fn': 'raw-proloog.gpx', 'loop': True},
    {'key': '1', 'num': 1, 'it': 'Etappe 1', 'fn': 'raw-etappe1.gpx', 'loop': False},
    {'key': '2', 'num': 2, 'it': 'Etappe 2', 'fn': 'raw-etappe2.gpx', 'loop': True},
    {'key': '3', 'num': 3, 'it': 'Etappe 3', 'fn': 'raw-etappe3.gpx', 'loop': False},
    {'key': '4', 'num': 4, 'it': 'Etappe 4', 'fn': 'raw-etappe4.gpx', 'loop': True, 'variant': 'A'},
    {'key': '4b', 'num': 4, 'it': 'Etappe 4', 'fn': 'raw-etappe4-afgekort.gpx', 'loop': True, 'variant': 'B'},
    {'key': '5', 'num': 5, 'it': 'Etappe 5', 'fn': 'raw-etappe5.gpx', 'loop': False},
]

# old climb-length hints (km), used to bound the backward search for a climb's base —
# real published lengths for these well-known passes, not something to re-derive blind.
CLIMB_LEN_HINT = {
    'Pian dei Pradi': 6.4, 'Passo del Compet': 10.2, 'Passo della Forcella': 12.3,
    'Passo Brocon': 18.7, 'Passo Gobbera': 7.0, 'Passo Sella': 14.6, 'Passo Gardena': 5.7,
    'Passo Valparola / Passo di Falzarego': 13.8, 'Passo Giau': 9.2, 'Passo di Fedaia': 14.0,
    'Passo Pordoi': 15.6, 'Passo San Pellegrino': 18.2, 'Passo Valles': 23.6,
    'Passo Cereda': 25.0, 'Passo Lavazè': 14.5, 'Passo Manghen': 16.2,
}

import re
CAT_RE = re.compile(r'CAT\s+(HC|\d)')
known_by_name_desc = {k['name']: k['desc'] for k in KNOWN_COLS}
def cat_for_known(name):
    m = CAT_RE.search(known_by_name_desc.get(name, ''))
    return m.group(1) if m else '?'

def nearest_idx_to_km(dists, km):
    lo, hi = 0, len(dists)-1
    # dists is monotonically increasing; binary search
    while lo < hi:
        mid = (lo+hi)//2
        if dists[mid]/1000.0 < km: lo = mid+1
        else: hi = mid
    return lo

def build_mapcoords(trkpts, target_n=400):
    n = len(trkpts)
    if n <= target_n:
        return [[round(p[0], 5), round(p[1], 5)] for p in trkpts]
    step = n / target_n
    out = []
    i = 0.0
    while int(i) < n:
        p = trkpts[int(i)]
        out.append([round(p[0], 5), round(p[1], 5)])
        i += step
    if [round(trkpts[-1][0], 5), round(trkpts[-1][1], 5)] != out[-1]:
        out.append([round(trkpts[-1][0], 5), round(trkpts[-1][1], 5)])
    return out

def build_profile(trkpts, dists, target_n=230):
    n = len(trkpts)
    pts = [(dists[i]/1000.0, trkpts[i][2]) for i in range(n) if trkpts[i][2] is not None]
    if len(pts) <= target_n:
        return [{'d': round(d,2), 'e': round(e)} for d,e in pts]
    step = len(pts) / target_n
    out = []
    i = 0.0
    while int(i) < len(pts):
        d, e = pts[int(i)]
        out.append({'d': round(d,2), 'e': round(e)})
        i += step
    last = pts[-1]
    if out[-1]['d'] != round(last[0],2):
        out.append({'d': round(last[0],2), 'e': round(last[1])})
    return out

WARN_LETOP = __import__('build_updates')

def build_stage(cfg):
    fn = cfg['fn']
    r = parse_full(fn)
    trkpts, dists = r['trkpts'], r['dists']
    pois = analyze_pois(fn)
    cols = match_cols(fn)

    start = {'lat': round(r['start'][0],6), 'lon': round(r['start'][1],6), 'ele': round(r['start'][2])}
    finish = {'lat': round(r['end'][0],6), 'lon': round(r['end'][1],6), 'ele': round(r['end'][2])}
    total_km = round(r['total_dist_km'], 1)

    vps_all = [p for p in pois if p['cat']=='vp']
    placeholders = [p for p in pois if p['cat']=='placeholder']

    # --- wxPoints + boundaries for segmentComposition ---
    boundaries = [('Start', 0.0)]
    wxPoints = [{'label':'Start','km':0.0,'ele':start['ele'],'lat':start['lat'],'lon':start['lon'],'idx':0}]
    vp_waypoints = []
    for i, vp in enumerate(vps_all[:2]):
        label = f'VP{i+1}'
        wxPoints.append({'label':label,'km':vp['km'],'ele':vp['ele'],'lat':vp['lat'],'lon':vp['lon'],'idx':i+1})
        vp_waypoints.append({'name':label,'type':'vp','lat':vp['lat'],'lon':vp['lon'],'ele':vp['ele'],'km':vp['km']})
        boundaries.append((label, vp['km']))
    tbd_note = None
    if placeholders:
        ph = placeholders[0]
        idx = len(vps_all[:2]) + 1  # next VP slot
        label = f'VP{idx}'
        wxPoints.append({'label':label,'km':ph['km'],'ele':ph['ele'],'lat':ph['lat'],'lon':ph['lon'],'idx':idx,'tbd':True})
        vp_waypoints.append({'name':label,'type':'vp','lat':ph['lat'],'lon':ph['lon'],'ele':ph['ele'],'km':ph['km'],'tbd':True})
        boundaries.append((label, ph['km']))
        tbd_note = f"{label} location unconfirmed (organizer placeholder in GPX at km {ph['km']})"
    wxPoints.append({'label':'Finish','km':total_km,'ele':finish['ele'],'lat':finish['lat'],'lon':finish['lon'],'idx':3})
    boundaries.append(('Finish', total_km))

    # --- segmentComposition via real speed curve ---
    segmentComposition = build_segments(fn, boundaries)

    # --- warnings + water combined into one list, same "km X,Y — text" inline
    # convention the app's existing s.warnings strings already use ---
    def fmt_km(km):
        return f"{km:.1f}".replace('.', ',')
    WATER_LABEL = {'Public Water Fountain': 'Drinkwaterpunt', 'Drinkfontein': 'Drinkfontein'}
    poi_raw = []
    for w in pois:
        if w['cat'] == 'warning':
            text = WARN_LETOP.clean_warning_text(w['name'], w['desc'])
            poi_raw.append((w['km'], 'warning', text))
        elif w['cat'] == 'water':
            label = WATER_LABEL.get((w['name'] or '').strip(), (w['name'] or 'Water').strip())
            poi_raw.append((w['km'], 'water', label))
    poi_raw.sort(key=lambda x: x[0])
    poi_list = [{'type': t, 'text': f"km {fmt_km(km)} — {txt}"} for km, t, txt in poi_raw]

    # --- cols: base + top + cat/pct, matched against known catalog. Base is placed at
    # the known real climb length back from the summit (established, published lengths
    # for these well-known passes) rather than a blind lowest-point search, which tends
    # to wander into earlier rolling terrain that isn't really "the climb" in the
    # commonly recognized sense.
    col_waypoints = []
    for c in cols:
        top_idx = nearest_idx_to_km(dists, c['km'])
        top_km = dists[top_idx]/1000.0
        hint = CLIMB_LEN_HINT.get(c['name'], 12.0)
        base_km = max(0.0, top_km - hint)
        base_idx = nearest_idx_to_km(dists, base_km)
        base_ele = trkpts[base_idx][2]
        length = round(top_km - dists[base_idx]/1000.0, 1)
        gain = c['ele_here'] - base_ele if base_ele else None
        avg_pct = round((gain/(length*1000))*100, 1) if gain and length>0 else None
        cat = cat_for_known(c['name'])
        pct_str = f"{avg_pct:.1f}".replace('.', ',') if avg_pct is not None else '?'
        len_str = f"{length:.1f}".replace('.', ',')
        col_waypoints.append({
            'name': c['name'], 'type':'col',
            'desc': f"CAT {cat} · {len_str} km, {pct_str}%",
            'ele': c['ele_here'], 'kmStart': round(dists[base_idx]/1000.0,1), 'kmTop': round(top_km,2),
            'lat': None, 'lon': None,  # filled from KNOWN_COLS below
            'profile': c['profile'],
        })
    known_by_name = {k['name']: k for k in KNOWN_COLS}
    for cw in col_waypoints:
        k = known_by_name[cw['name']]
        cw['lat'] = k['lat']; cw['lon'] = k['lon']

    mapCoords = build_mapcoords(trkpts)
    profile = build_profile(trkpts, dists)

    return {
        'key': cfg['key'], 'num': cfg['num'], 'it': cfg['it'], 'variant': cfg.get('variant'),
        'dist': total_km, 'gain': round(r['gain_m']), 'loss': round(r['loss_m']),
        'maxElev': round(r['max_ele']), 'minElev': round(r['min_ele']),
        'start': start, 'finish': finish,
        'wxPoints': wxPoints, 'vp_waypoints': vp_waypoints, 'tbd_note': tbd_note,
        'segmentComposition': segmentComposition,
        'poi_list': poi_list,
        'col_waypoints': col_waypoints,
        'mapCoords': mapCoords, 'profile': profile,
        'n_mapCoords': len(mapCoords), 'n_profile': len(profile),
    }

if __name__ == '__main__':
    out = {}
    for cfg in STAGES:
        print("building", cfg['key'], cfg['it'], cfg.get('variant',''))
        out[cfg['key']] = build_stage(cfg)
    with open('full_build.json','w',encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print("done ->  full_build.json")
