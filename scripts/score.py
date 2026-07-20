#!/usr/bin/env python3
"""Deterministic Upside Score computation for Chennai Real Estate Intelligence.

Reads docs/data/projects.json, localities.json, infrastructure.json and rewrites
projects.json in place with upside_score, score_breakdown, risk, tags, and
score_rationale recomputed from the raw fields. Re-running with unchanged inputs
produces unchanged output, so every refresh stays reviewable as a clean diff.

Usage: python3 scripts/score.py
"""
import json
import math
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA = os.path.join(ROOT, 'docs', 'data')

# Developer tiers drive the track-record factor. Tier 1: large, established
# delivery record at scale. Tier 2: established regional players. Anyone not
# listed is tier 3 (unknown/small — scores low, risk-flagged).
TIER1 = {
    'casagrand', 'prestige', 'brigade', 'godrej', 'tvs emerald', 'appaswamy',
    'sobha', 'l&t realty', 'mahindra', 'puravankara', 'provident', 'dlf',
    'tata housing', 'hiranandani',
}
TIER2 = {
    'radiance', 'dra', 'urbanrise', 'alliance', 'shriram', 'jain housing',
    'jains', 'vgn', 'g square', 'akshaya', 'dac', 'baashyaam', 'lancor',
    'ceebros', 'navins', 'arihant', 'olympia', 'kg ', 'spr', 'emerald haven',
}

STAGE_POINTS = {
    'pre-launch': 25, 'new-launch': 21, 'under-construction': 12,
    'nearing-possession': 5, 'completed': 2,
}
TREND_POINTS = {'rising-fast': 20, 'rising': 15, 'stable': 9, 'soft': 3}


def load(name):
    with open(os.path.join(DATA, name)) as f:
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


def pricing_points(p, loc):
    pmin, pmax = p.get('price_sqft_min'), p.get('price_sqft_max')
    if pmin is None or not loc or loc.get('price_band_min') is None or loc.get('price_band_max') is None:
        return 7
    proj_mid = (pmin + (pmax or pmin)) / 2
    band_mid = (loc['price_band_min'] + loc['price_band_max']) / 2
    if band_mid <= 0:
        return 7
    ratio = proj_mid / band_mid
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


def main():
    projects = load('projects.json')
    localities = load('localities.json')
    infrastructure = load('infrastructure.json')

    loc_by_name = {l['name'].lower(): l for l in localities['localities']}

    # Collect every station / point / waypoint as an upside anchor.
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

        bd = {
            'entry_stage': STAGE_POINTS.get(p.get('stage'), 10),
            'infrastructure': infra_points_for(p, infra_points),
            'locality_momentum': TREND_POINTS.get(loc.get('trend'), 8) if loc else 8,
            'relative_pricing': pricing_points(p, loc),
            'developer_track_record': {1: 10, 2: 7, 3: 3}[tier],
            'rental_yield': yield_points(loc),
        }
        score = sum(bd.values())
        p['score_breakdown'] = bd
        p['upside_score'] = score

        # Risk: count independent red flags.
        flood = (loc or {}).get('flood_risk', 'unknown')
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

    save('projects.json', projects)
    scored = [p['upside_score'] for p in projects['projects']]
    print(f"Scored {len(scored)} projects; range {min(scored)}-{max(scored)}, "
          f"mean {sum(scored)/len(scored):.1f}")


if __name__ == '__main__':
    main()
