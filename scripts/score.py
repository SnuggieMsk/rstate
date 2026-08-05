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

# Canonical developer name -> substrings that identify it in a raw promoter string.
# Promoter strings from the RERA registry are full legal names ("M/s Casagrand
# Astute Pvt Ltd Rep By its Director…"), so matching is substring-based and
# ordered: the first canonical name whose any-substring matches wins.
DEVELOPER_ALIASES = [
    ('Casagrand', ['casagrand']),
    ('Prestige Group', ['prestige estates', 'prestige projects', 'prestige group', 'prestige ']),
    ('Brigade Group', ['brigade enterprises', 'brigade group', 'brigade ']),
    ('Godrej Properties', ['godrej']),
    ('TVS Emerald', ['tvs emerald', 'emerald haven']),
    ('Appaswamy Real Estates', ['appaswamy']),
    ('Sobha', ['sobha']),
    ('L&T Realty', ['l&t realty', 'l & t realty', 'lnt realty', 'larsen & toubro realty']),
    ('Puravankara / Provident', ['puravankara', 'provident housing', 'provident ']),
    ('Mahindra Lifespaces', ['mahindra lifespace', 'mahindra world city', 'mahindra residential']),
    ('DLF', ['dlf ']),
    ('Tata Housing', ['tata housing', 'tata realty']),
    ('Hiranandani', ['hiranandani']),
    ('Radiance Realty', ['radiance']),
    ('DRA Homes', ['dra homes', 'dra smart', 'd.r.a', 'dra ']),
    ('Urbanrise / Alliance', ['urbanrise', 'alliance group', 'alliance infrastructure']),
    ('Shriram Properties', ['shriram propert', 'shriram housing']),
    ('Jain Housing', ['jain housing', "jain's", 'jains ']),
    ('VGN Homes', ['vgn ']),
    ('G Square Housing', ['g square', 'gsquare']),
    ('Akshaya Homes', ['akshaya']),
    ('DAC Developers', ['dac developers', 'dac ']),
    ('Baashyaam', ['baashyaam', 'bhaashyam']),
    ('Lancor Holdings', ['lancor']),
    ("Navin's", ['navin housing', "navin's", 'navins']),
    ('Arihant Foundations', ['arihant']),
    ('Olympia Group', ['olympia']),
    ('KG Foundations', ['kg foundations', 'kg builders']),
    ('SPR India', ['spr india', 'spr city', 'spr highliving', 'spr ']),
    ('Ceebros', ['ceebros']),
    ('ASV Constructions', ['asv ']),
    ('True Value Homes', ['true value homes', 'tvh ']),
    ('Ozone Group', ['ozone ']),
    ('Doshi Housing', ['doshi']),
    ('Rajparis', ['rajparis']),
    ('India Builders', ['india builders']),
    ('Ruby Builders', ['ruby builders']),
    ('Vijay Shanthi', ['vijay shanthi', 'vijayshanthi']),
    ('Alliance Infra', ['alliance ']),
    ('Sumanth & Co', ['sumanth']),
    ('Landmark Housing', ['landmark housing']),
    ('Marg', ['marg ltd', 'marg limited', 'marg properties']),
    ('Unitech', ['unitech']),
]

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


# Records kept for history but excluded from every rollup and ranking. Mirrors
# RETIRED in docs/assets/app.js — keep the two in step.
RETIRED_STATUS = {'withdrawn', 'superseded', 'unverified'}


def canonical_developer(promoter):
    """Map a raw promoter string to a canonical developer name for filtering."""
    s = (promoter or '').lower()
    if not s.strip():
        return None
    # An alias must match a WHOLE word at both ends. Plain substring matching
    # wrongly attributed "MahenDRA Kumar Gupta" to DRA Homes and, worse, the
    # individual promoter "Kalpesh SOBHAgmal" to Sobha Ltd.
    for canon, keys in DEVELOPER_ALIASES:
        if any(re.search(r'(?<![a-z])' + re.escape(k) + r'(?![a-z])', s) for k in keys):
            return canon
    # Fall back to a cleaned-up version of the raw legal name so every project
    # still lands under some developer bucket.
    t = re.sub(r'\b(m/s\.?|messrs\.?)\b', ' ', promoter or '', flags=re.I)
    t = re.split(r'\brep(?:resented)?\.?\s+by\b|,|\(', t, maxsplit=1)[0]
    t = re.sub(r'\b(private|pvt|limited|ltd|llp|company|co|and|&)\b\.?', ' ', t, flags=re.I)
    t = re.sub(r'[^A-Za-z0-9&.\' ]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip(' .&')
    # A one- or two-character residue is noise, not a developer name.
    if len(t) < 3 or not re.search(r'[A-Za-z]{3}', t):
        return None
    return t.title() if t.isupper() or t.islower() else t


def developer_tier(promoter):
    s = (promoter or '').lower()
    if any(t in s for t in TIER1):
        return 1
    if any(t in s for t in TIER2):
        return 2
    return 3


def price_band_for(p, loc):
    """Pick the locality band that is comparable to this project's own rate.

    A plotted layout quotes a rate per sqft of LAND; an apartment quotes a rate per
    sqft of BUILT-UP area. In Chennai the land rate is routinely a third of the
    built-up rate in the same locality, so scoring a plot against the apartment band
    reads every layout as a huge discount. Compare like with like, and where the
    matching band has not been researched, decline to score rather than guess.
    """
    if not loc:
        return None
    lo, hi = ('plot_band_min', 'plot_band_max') if p.get('type') == 'plotted' \
        else ('price_band_min', 'price_band_max')
    if loc.get(lo) is None or loc.get(hi) is None:
        return None
    return loc[lo], loc[hi]


def pricing_ratio(p, loc):
    pmin, pmax = p.get('price_sqft_min'), p.get('price_sqft_max')
    band = price_band_for(p, loc)
    if pmin is None or band is None:
        return None
    band_mid = (band[0] + band[1]) / 2
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


def distressed_persona_fit(d):
    """Bucket a distressed/deal record into the same three client-lens personas
    used for projects, so the Deals page persona switcher has something to filter on."""
    fits = set()
    if d.get('record_type') == 'auction':
        reserve = d.get('reserve_price_inr')
        ticket_lakh = reserve / 1e5 if reserve else None
        if ticket_lakh is None:
            fits.add('value')
        elif ticket_lakh >= 100:
            fits.add('boardroom')
        elif ticket_lakh >= 30:
            fits.add('executive')
        else:
            fits.add('value')
        if (d.get('discount_pct') or 0) >= 40:
            fits.add('value')
    else:
        text = ((d.get('opportunity_note') or '') + ' ' + (d.get('status_2026') or '')).lower()
        if re.search(r'institutional|nclt (?:resolution|bid)|resolution applicant|large-hni', text):
            fits.add('boardroom')
        if re.search(r'resale|retail|delivered tower|discount|bulk purchase', text):
            fits.add('value')
        if not fits:
            fits.add('value')
    return sorted(fits)


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
    # Fall back to the locality-benchmark estimate so a registry record can still be
    # placed in a client bracket. Which buyer a project suits is a judgement the
    # estimate supports; how cheap it is for its locality is not, which is why
    # relative_pricing above reads the researched price only.
    tmin = p.get('ticket_min_lakh') or p.get('est_ticket_min_lakh')
    tmax = p.get('ticket_max_lakh') or p.get('est_ticket_max_lakh')
    psq = p.get('price_sqft_min') or p.get('est_price_sqft_min')
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
        p['developer'] = canonical_developer(p.get('promoter'))

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

        # Housing that is allotted rather than sold suits no client segment —
        # there is nothing to buy.
        seg = ({'boardroom': 0, 'executive': 0, 'value': 0} if p.get('not_for_sale')
               else segment_fit(p, loc, tier, ratio))
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

    # Distressed: compute discount vs locality band for built assets (flat/house),
    # then bucket every record into the same Boardroom/Executive/Value personas as projects.
    if distressed:
        for d in distressed.get('distressed', []):
            d.pop('discount_pct', None)
            d.pop('value_note', None)
            if d.get('record_type') == 'auction':
                loc = loc_by_name.get((d.get('band_locality') or d.get('locality') or '').lower())
                area, reserve = d.get('area_sqft'), d.get('reserve_price_inr')
                if (d.get('asset_type') in ('flat', 'house') and loc and area and reserve
                        and loc.get('price_band_min') and loc.get('price_band_max')):
                    band_mid = (loc['price_band_min'] + loc['price_band_max']) / 2
                    est = band_mid * area
                    d['discount_pct'] = round((1 - reserve / est) * 100)
                    d['value_note'] = (f'Reserve ₹{reserve/1e5:.1f}L vs ~₹{est/1e5:.0f}L at the '
                                       f'{loc["name"]} band midpoint (₹{band_mid:,.0f}/sqft × {area:,} sqft)')
            d['persona_fit'] = distressed_persona_fit(d)
        save('distressed.json', distressed)

    # ---- Developer rollups -------------------------------------------------
    # Researched profile fields (delivery reputation, red flags, tier signal) are
    # preserved; portfolio stats are always recomputed from the current projects.
    devs = load('developers.json') or {'developers': []}
    profiles = {d['name']: d for d in devs.get('developers', [])}
    STAT_KEYS = ('project_count', 'active_projects', 'zones', 'localities', 'stage_mix',
                 'avg_upside_score', 'best_project', 'ticket_min_lakh', 'ticket_max_lakh',
                 'segments', 'rera_registered_count', 'high_risk_count')
    by_dev = {}
    for p in projects['projects']:
        if not p.get('developer'):
            continue
        by_dev.setdefault(p['developer'], []).append(p)

    out_devs = []
    for name, plist in sorted(by_dev.items()):
        prof = profiles.get(name, {'name': name})
        for k in STAT_KEYS:
            prof.pop(k, None)
        active = [p for p in plist if p.get('status') not in RETIRED_STATUS]
        scores = [p['upside_score'] for p in active if p.get('upside_score') is not None]
        tickets_lo = [p['ticket_min_lakh'] for p in active if p.get('ticket_min_lakh')]
        tickets_hi = [p['ticket_max_lakh'] for p in active if p.get('ticket_max_lakh')]
        best = max(active, key=lambda p: p.get('upside_score') or 0, default=None)
        stage_mix = {}
        for p in active:
            stage_mix[p.get('stage') or 'unknown'] = stage_mix.get(p.get('stage') or 'unknown', 0) + 1
        seg = set()
        for p in active:
            for s in ('Boardroom', 'Executive', 'Value'):
                if s in (p.get('tags') or []):
                    seg.add(s.lower())
        prof.update({
            'name': name,
            'project_count': len(plist),
            'active_projects': len(active),
            'zones': sorted({p['corridor'] for p in active if p.get('corridor')}),
            'localities': sorted({p['locality'] for p in active if p.get('locality')}),
            'stage_mix': stage_mix,
            'avg_upside_score': round(sum(scores) / len(scores)) if scores else None,
            'best_project': {'name': best['name'], 'id': best['id'],
                             'score': best.get('upside_score')} if best else None,
            'ticket_min_lakh': min(tickets_lo) if tickets_lo else None,
            'ticket_max_lakh': max(tickets_hi) if tickets_hi else None,
            'segments': sorted(seg),
            'rera_registered_count': sum(1 for p in active if p.get('rera_no')),
            'high_risk_count': sum(1 for p in active if p.get('risk') == 'High'),
        })
        out_devs.append(prof)

    # Keep researched profiles for developers with no tracked project (e.g. groups
    # that have exited Chennai but whose history still matters to a buyer).
    covered = {d['name'] for d in out_devs}
    for name, prof in profiles.items():
        if name in covered:
            continue
        if not (prof.get('delivery_reputation') or prof.get('red_flags')):
            continue
        prof.update({
            'project_count': 0, 'active_projects': 0, 'zones': [], 'localities': [],
            'stage_mix': {}, 'avg_upside_score': None, 'best_project': None,
            'ticket_min_lakh': None, 'ticket_max_lakh': None, 'segments': [],
            'rera_registered_count': 0, 'high_risk_count': 0, 'profile_only': True,
        })
        out_devs.append(prof)
    out_devs.sort(key=lambda d: d['name'])
    save('developers.json', {'developers': out_devs})

    save('projects.json', projects)
    save('localities.json', localities)
    scored = [p['upside_score'] for p in projects['projects']]
    n_seg = {s: sum(1 for p in projects['projects'] if s.title() in p['tags'])
             for s in ('boardroom', 'executive', 'value')}
    print(f"Scored {len(scored)} projects; range {min(scored)}-{max(scored)}, "
          f"mean {sum(scored)/len(scored):.1f}; segments {n_seg}")
    if distressed:
        discounted = [d for d in distressed['distressed'] if d.get('discount_pct') is not None]
        d_seg = {s: sum(1 for d in distressed['distressed'] if s in (d.get('persona_fit') or []))
                 for s in ('boardroom', 'executive', 'value')}
        print(f"Distressed: {len(distressed['distressed'])} records, "
              f"{len(discounted)} with computed discount, persona_fit {d_seg}")


if __name__ == '__main__':
    main()
