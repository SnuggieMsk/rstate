#!/usr/bin/env python3
"""Deterministic scoring for Chennai Real Estate Intelligence.

Reads docs/data/{projects,localities,infrastructure,distressed}.json and rewrites
projects.json, localities.json, and distressed.json in place with computed fields:
  projects:   upside_score, score_breakdown, risk, tags, score_rationale,
              segment_fit {boardroom, executive, value}
  localities: tier (Prime/Established/Growth/Emerging)
  distressed: discount_pct (auction reserve vs locality price band), value_note
Re-running with unchanged inputs produces unchanged output.

Usage: python3 scripts/score.py
"""
import json
import math
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA = os.path.join(ROOT, 'docs', 'data')

TIER1 = {
    'casagrand', 'prestige', 'brigade', 'godrej', 'tvs emerald', 'appaswamy',
    'sobha', 'l&t realty', 'mahindra', 'puravankara', 'provident', 'dlf',
    'tata housing', 'hiranandani',
}
TIER2 = {
    'radiance', 'dra', 'urbanrise', 'alliance', 'shriram', 'jain housing',
    'jains', 'vgn', 'g square', 'akshaya', 'dac', 'baashyaam', 'lancor',
    'ceebros', 'navins', 'navin', 'arihant', 'olympia', 'kg ', 'spr',
    'emerald haven',
}

STAGE_POINTS = {
    'pre-launch': 25, 'new-launch': 21, 'under-construction': 12,
    'nearing-possession': 5, 'completed': 2,
}
TREND_POINTS = {'rising-fast': 20, 'rising': 15, 'stable': 9, 'soft': 3,
                'cooling': 6, 'falling': 2}

# Boardroom = ₹3Cr+ exclusive 3-4BHK; Executive = ₹1-2.5Cr 2-3BHK; thresholds in lakh.
BOARDROOM_TICKET_LAKH = 300
EXEC_TICKET_RANGE = (90, 260)


def load(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def save(name, obj):
    with open(os.path.join(DATA, name), 'w') as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write('\n')


def km(lat1, lng1, lat2, lng2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def infra_points_for(p, infra_points):
    if p.get('lat') is None or p.get('lng') is None or not infra_points:
        return 8
    d = min(km(p['lat'], p['lng'], lat, lng) for lat, lng in infra_points)
    if d < 1.0:
        return 20
    if d < 2.5:
        return 16
    if d < 5.0:
        return 12
    if d < 10.0:
        return 7
    return 3


def developer_tier(promoter):
    s = (promoter or '').lower()
    if any(t in s for t in TIER1):
        return 1
    if any(t in s for t in TIER2):
        return 2
    return 3


def pricing_ratio(p, loc):
    pmin, pmax = p.get('price_sqft_min'), p.get('price_sqft_max')
    if pmin is None or not loc or loc.get('price_band_min') is None or loc.get('price_band_max') is None:
        return None
    band_mid = (loc['price_band_min'] + loc['price_band_max']) / 2
    if band_mid <= 0:
        return None
    return ((pmin + (pmax or pmin)) / 2) / band_mid


def pricing_points(ratio):
    if ratio is None:
        return 7
    if ratio < 0.85:
        return 15
    if ratio < 1.0:
        return 12
    if ratio < 1.15:
        return 8
    return 4


def yield_points(loc):
    y = loc.get('rental_yield_pct') if loc else None
    if y is None:
        return 5
    if y >= 4.0:
        return 10
    if y >= 3.5:
        return 8
    if y >= 3.0:
        return 6
    return 4


def locality_tier(loc):
    top = loc.get('price_band_max')
    if top is None:
        return 'Emerging'
    if top >= 14000:
        return 'Prime'
    if top >= 8000:
        return 'Established'
    if top >= 5000:
        return 'Growth'
    return 'Emerging'


def loc_segments(loc):
    """Normalize a locality's segment_fit into a set (agents returned arrays or strings)."""
    raw = (loc or {}).get('segment_fit') or []
    if isinstance(raw, str):
        raw = re.findall(r'boardroom|executive|value', raw.lower())
    return {s.lower() for s in raw}


def segment_fit(p, loc, tier, ratio):
    tmin, tmax = p.get('ticket_min_lakh'), p.get('ticket_max_lakh')
    psq = p.get('price_sqft_min')
    dom = (p.get('dominant_config') or '').lower()
    cfg = (p.get('config_mix') or '').lower()
    units = p.get('total_units')
    ltier = locality_tier(loc) if loc else 'Emerging'
    lsegs = loc_segments(loc)
    dev = developer_tier(p.get('promoter'))

    b = 0
    if (tmax or 0) >= BOARDROOM_TICKET_LAKH or (psq or 0) >= 12000:
        b += 40
    if dom in ('3bhk', '4bhk+', 'villa') or re.search(r'4\s*bhk|villa|duplex|penthouse', cfg):
        b += 20
    if ltier == 'Prime' or 'boardroom' in lsegs:
        b += 20
    if units is not None and units <= 150:
        b += 10
    if dev == 1:
        b += 10

    e = 0
    lo, hi = EXEC_TICKET_RANGE
    if (tmin is not None and tmax is not None and tmin <= hi and tmax >= lo) or \
       (tmin is None and psq is not None and 6000 <= psq < 12000):
        e += 30
    if dom in ('2bhk', '3bhk') or re.search(r'[23]\s*bhk', cfg) or p.get('type') == 'apartment':
        e += 20
    if (loc or {}).get('rental_yield_pct') and loc['rental_yield_pct'] >= 3.5 or 'executive' in lsegs:
        e += 20
    if p.get('stage') in ('new-launch', 'under-construction', 'pre-launch'):
        e += 15
    if dev <= 2:
        e += 15
    if (tmin or 0) >= BOARDROOM_TICKET_LAKH:  # pure ultra-luxury is not an Executive pick
        e = min(e, 45)

    v = 0
    if ratio is not None and ratio < 0.9:
        v += 50
    elif ratio is not None and ratio < 1.0:
        v += 30
    if 'value' in lsegs:
        v += 30
    if psq is not None and loc and loc.get('price_band_min') and psq < loc['price_band_min']:
        v += 20

    return {'boardroom': min(b, 100), 'executive': min(e, 100), 'value': min(v, 100)}


def main():
    projects = load('projects.json')
    localities = load('localities.json')
    infrastructure = load('infrastructure.json')
    distressed = load('distressed.json')

    for l in localities['localities']:
        l['tier'] = locality_tier(l)
    loc_by_name = {l['name'].lower(): l for l in localities['localities']}

    infra_points = []
    for inf in infrastructure['infrastructure']:
        g = inf.get('geometry') or {}
        if g.get('type') == 'stations':
            infra_points += [(s['lat'], s['lng']) for s in g.get('stations', [])
                             if s.get('lat') is not None]
        elif g.get('type') == 'polyline':
            infra_points += [(w['lat'], w['lng']) for w in g.get('waypoints', [])
                             if w.get('lat') is not None]
        elif g.get('lat') is not None:
            infra_points.append((g['lat'], g['lng']))

    for p in projects['projects']:
        loc = loc_by_name.get((p.get('locality') or '').lower())
        tier = developer_tier(p.get('promoter'))
        ratio = pricing_ratio(p, loc)

        bd = {
            'entry_stage': STAGE_POINTS.get(p.get('stage'), 10),
            'infrastructure': infra_points_for(p, infra_points),
            'locality_momentum': TREND_POINTS.get((loc or {}).get('trend'), 8),
            'relative_pricing': pricing_points(ratio),
            'developer_track_record': {1: 10, 2: 7, 3: 3}[tier],
            'rental_yield': yield_points(loc),
        }
        score = sum(bd.values())
        p['score_breakdown'] = bd
        p['upside_score'] = score

        seg = segment_fit(p, loc, tier, ratio)
        p['segment_fit'] = seg

        flood = (loc or {}).get('flood_risk', 'unknown')
        if isinstance(flood, str) and flood not in ('low', 'medium', 'high'):
            flood = 'medium' if 'moderate' in flood else ('high' if 'high' in flood else 'low')
        flags = 0
        if not p.get('rera_no'):
            flags += 1
        if flood == 'high':
            flags += 1
        if tier == 3:
            flags += 1
        if 'oversupply' in ((loc or {}).get('supply_note') or '').lower():
            flags += 1
        p['risk'] = 'Low' if flags == 0 else ('Medium' if flags == 1 else 'High')

        tags = []
        if p.get('stage') in ('pre-launch', 'new-launch'):
            tags.append('Early Entrant')
        if score >= 78:
            tags.append('High Upside')
        if seg['boardroom'] >= 60:
            tags.append('Boardroom')
        if seg['executive'] >= 60:
            tags.append('Executive')
        if seg['value'] >= 60:
            tags.append('Value')
        if p.get('type') == 'plotted':
            tags.append('Plotted/Land')
        if (p.get('price_sqft_min') or 0) >= 12000:
            tags.append('Premium')
        if loc and (loc.get('rental_yield_pct') or 0) >= 3.5 and p.get('stage') in (
                'under-construction', 'nearing-possession'):
            tags.append('Steady/Rental')
        if p['risk'] == 'High':
            tags.append('Watchlist/Risky')
        p['tags'] = tags

        why = []
        if bd['entry_stage'] >= 21:
            why.append('early entry stage')
        if bd['infrastructure'] >= 16:
            why.append('close to upcoming metro/infrastructure')
        if bd['locality_momentum'] >= 15:
            why.append('rising micro-market')
        if bd['relative_pricing'] >= 12:
            why.append('priced below the locality band')
        if bd['developer_track_record'] >= 10:
            why.append('strong developer record')
        caveats = []
        if not p.get('rera_no'):
            caveats.append('RERA number not yet found')
        if flood == 'high':
            caveats.append('flood-prone zone')
        if tier == 3:
            caveats.append('limited developer track record')
        rationale = ('Scores on ' + ', '.join(why) + '.') if why else 'No strong upside signals under the rule set.'
        if caveats:
            rationale += ' Caveats: ' + ', '.join(caveats) + '.'
        p['score_rationale'] = rationale

    # Distressed: compute discount vs locality band for built assets (flat/house).
    if distressed:
        for d in distressed.get('distressed', []):
            d.pop('discount_pct', None)
            d.pop('value_note', None)
            if d.get('record_type') != 'auction':
                continue
            loc = loc_by_name.get((d.get('band_locality') or d.get('locality') or '').lower())
            area, reserve = d.get('area_sqft'), d.get('reserve_price_inr')
            if (d.get('asset_type') in ('flat', 'house') and loc and area and reserve
                    and loc.get('price_band_min') and loc.get('price_band_max')):
                band_mid = (loc['price_band_min'] + loc['price_band_max']) / 2
                est = band_mid * area
                d['discount_pct'] = round((1 - reserve / est) * 100)
                d['value_note'] = (f'Reserve ₹{reserve/1e5:.1f}L vs ~₹{est/1e5:.0f}L at the '
                                   f'{loc["name"]} band midpoint (₹{band_mid:,.0f}/sqft × {area:,} sqft)')
        save('distressed.json', distressed)

    save('projects.json', projects)
    save('localities.json', localities)
    scored = [p['upside_score'] for p in projects['projects']]
    n_seg = {s: sum(1 for p in projects['projects'] if s.title() in p['tags'])
             for s in ('boardroom', 'executive', 'value')}
    print(f"Scored {len(scored)} projects; range {min(scored)}-{max(scored)}, "
          f"mean {sum(scored)/len(scored):.1f}; segments {n_seg}")
    if distressed:
        discounted = [d for d in distressed['distressed'] if d.get('discount_pct') is not None]
        print(f"Distressed: {len(distressed['distressed'])} records, "
              f"{len(discounted)} with computed discount")


if __name__ == '__main__':
    main()
