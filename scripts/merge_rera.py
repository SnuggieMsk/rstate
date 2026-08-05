#!/usr/bin/env python3
"""Merge scraped TNRERA registry records (.cache/rera_scraped.json) into
docs/data/projects.json.

Registry records carry real RERA numbers, promoters, and village/taluk locations
but no pricing, so they are added as `source: "rera-registry"` and left for
scripts/score.py to score with its neutral defaults. Existing curated records
(`source: "curated"`) are never overwritten — a registry hit on an existing
project only backfills its RERA number and location if those were missing.

Usage: python3 scripts/merge_rera.py [--dry-run]
"""
import argparse
import json
import os
import re
import unicodedata

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA = os.path.join(ROOT, 'docs', 'data')
SCRAPED = os.path.join(ROOT, '.cache', 'rera_scraped.json')

# Fallback centroids when a village cannot be matched to a tracked locality.
TALUK_CENTROIDS = {
    'ambattur': (13.114, 80.148), 'alandur': (13.003, 80.201), 'aminjikarai': (13.072, 80.229),
    'ayanavaram': (13.100, 80.235), 'egmore': (13.073, 80.261), 'guindy': (13.007, 80.221),
    'madhavaram': (13.148, 80.231), 'maduravoyal': (13.065, 80.169), 'mambalam': (13.041, 80.221),
    'mylapore': (13.034, 80.269), 'perambur': (13.108, 80.232), 'purasawalkam': (13.088, 80.254),
    'sholinganallur': (12.901, 80.227), 'thiruvottiyur': (13.161, 80.302), 'tondiarpet': (13.128, 80.284),
    'velachery': (12.976, 80.220), 'sriperumbudur': (12.968, 79.947), 'kancheepuram': (12.834, 79.704),
    'chengalpattu': (12.682, 79.986), 'tambaram': (12.925, 80.117), 'pallavaram': (12.967, 80.150),
    'thiruporur': (12.726, 80.191), 'tiruvallur': (13.143, 79.909), 'poonamallee': (13.048, 80.095),
    'avadi': (13.115, 80.097), 'gummidipoondi': (13.408, 80.109), 'ponneri': (13.338, 80.195),
    'uthukottai': (13.334, 79.888), 'pallipattu': (13.336, 79.436), 'r.k. pet': (13.427, 79.729),
    'vandalur': (12.892, 80.081), 'madurantakam': (12.508, 79.885), 'cheyyur': (12.345, 79.999),
    'tirukalukundram': (12.610, 80.062), 'walajabad': (12.792, 79.825), 'uthiramerur': (12.616, 79.755),
    'sunguvarchatram': (12.855, 79.936), 'kundrathur': (12.995, 80.100), 'thirukazhukundram': (12.610, 80.062),
    'alandur taluk': (13.003, 80.201),
}
DISTRICT_CENTROIDS = {
    'Chennai': (13.070, 80.240), 'Kancheepuram': (12.834, 79.704),
    'Tiruvallur': (13.143, 79.909), 'Chengalpattu': (12.682, 79.986),
}
DISTRICT_ZONE = {
    'Chennai': 'Central Chennai', 'Kancheepuram': 'Kanchipuram',
    'Tiruvallur': 'Far West', 'Chengalpattu': 'GST Road',
}


def clean(s):
    if not isinstance(s, str):
        return s
    s = unicodedata.normalize('NFKC', s).replace('&amp;', '&')
    return re.sub(r'\s+', ' ', s).strip()


def titlecase(s):
    s = clean(s) or ''
    return s.title() if (s.isupper() or s.islower()) else s


def clean_place(s):
    """Registry address fields carry trailing noise ('Pincode: 600091', 'Village')."""
    s = clean(s) or ''
    # Some registry values run one field into the next when the source omits a comma.
    s = re.split(r'\bpincode\b|\bpin\b|\bdistrict\b|\btaluk\b|\bstate\b|\bcity\s*[:/]', s, flags=re.I)[0]
    s = re.sub(r'\b(village|post|town|city|vill\.?)\b\.?\s*$', '', s, flags=re.I)
    s = re.sub(r'^(s\.?no\.?|survey no\.?)[:\s]*', '', s, flags=re.I)
    return re.sub(r'[\s,.:;-]+$', '', s).strip()


def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', (name or '').lower()).strip('-')[:60]


STOP = {'the', 'at', 'of', 'phase', 'project', 'residency', 'apartments', 'apartment'}


def name_key(name):
    words = re.findall(r'[a-z0-9]+', re.sub(r'\(.*?\)', '', (name or '').lower()))
    return frozenset(w.rstrip('s') if len(w) > 3 else w for w in words if w not in STOP)


def stage_from(status_raw, reg_year, record_type='building'):
    """A layout's registry status is 'completed' once the layout is approved, which
    says nothing about entry timing — for plots, recency of registration is the
    signal, so status is only consulted for buildings."""
    s = (status_raw or '').lower()
    if record_type != 'layout' and 'complete' in s:
        return 'completed'
    if reg_year and reg_year >= '2026':
        return 'new-launch'
    if reg_year and reg_year >= '2025':
        return 'under-construction'
    return 'completed' if record_type != 'layout' else 'under-construction'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    with open(SCRAPED) as f:
        scraped = json.load(f)
    with open(os.path.join(DATA, 'projects.json')) as f:
        pdata = json.load(f)
    with open(os.path.join(DATA, 'localities.json')) as f:
        localities = json.load(f)['localities']

    projects = pdata['projects']
    for p in projects:
        p.setdefault('source', 'curated')

    # Locality lookup by normalized name, longest-first so "West Tambaram" beats "Tambaram".
    loc_index = sorted(((norm(l['name']), l) for l in localities), key=lambda x: -len(x[0]))
    by_rera = {(p.get('rera_no') or '').upper().replace('TN/', 'TNRERA/').replace('/BUILDING/', '/BLG/'): p
               for p in projects if p.get('rera_no')}
    by_name = {}
    for p in projects:
        by_name.setdefault(name_key(p['name']), p)

    def match_locality(*candidates):
        for cand in candidates:
            n = norm(cand)
            if not n:
                continue
            for ln, l in loc_index:
                if ln and (ln == n or ln in n or n in ln):
                    return l
        return None

    added, backfilled, skipped = [], 0, 0
    for r in scraped['projects']:
        rera = r['rera_no']
        name = titlecase(r.get('name') or '')
        if not name:
            skipped += 1
            continue

        existing = by_rera.get(rera) or by_name.get(name_key(name))
        if existing:
            # Curated record wins; only fill gaps.
            if not existing.get('rera_no'):
                existing['rera_no'] = rera
                existing.setdefault('sources', []).append(r['url'])
                backfilled += 1
            continue

        village_c = clean_place(r.get('village'))
        city_c = clean_place(r.get('city'))
        taluk_c = clean_place(r.get('taluk'))
        loc = match_locality(village_c, city_c, taluk_c)
        district = clean(r.get('district')) or ''
        if loc:
            locality, corridor = loc['name'], loc.get('corridor')
            lat, lng, precision = loc.get('lat'), loc.get('lng'), 'approximate'
        else:
            village = titlecase(village_c or city_c or taluk_c or district or 'Chennai')
            locality = village
            corridor = DISTRICT_ZONE.get(district, 'Chennai (other)')
            tal = taluk_c.lower().strip()
            pt = TALUK_CENTROIDS.get(tal) or DISTRICT_CENTROIDS.get(district) or (13.07, 80.24)
            lat, lng = pt
            precision = 'taluk' if tal in TALUK_CENTROIDS else 'district'

        promoter = titlecase(re.split(r'\brep(?:resented)?\.?\s+by\b', clean(r.get('promoter_legal') or r.get('promoter') or ''), maxsplit=1, flags=re.I)[0])
        rec = {
            'id': slug(name) + '-' + rera.split('/')[-2],
            'name': name,
            'promoter': promoter or None,
            'rera_no': rera,
            'registration_date': r.get('reg_year'),
            'type': 'plotted' if r.get('record_type') == 'layout' else (r.get('type') or 'apartment'),
            'locality': locality,
            'corridor': corridor,
            'lat': lat, 'lng': lng, 'geo_precision': precision,
            'total_units': r.get('total_units'),
            'price_sqft_min': None, 'price_sqft_max': None, 'ticket_note': None,
            'expected_completion': r.get('completion_raw'),
            'stage': stage_from(r.get('status_raw'), r.get('reg_year'), r.get('record_type', 'building')),
            'status': 'active',
            'data_confidence': 'reported',
            'source': 'rera-registry',
            'sources': [r['url']],
            'notes': ' · '.join(filter(None, [
                ('TNRERA plotted-layout registration' if r.get('record_type') == 'layout'
                 else 'TNRERA building registration')
                + f" ({district} district"
                + (f", {titlecase(taluk_c)} taluk" if taluk_c else '') + ')',
                f"Village: {titlecase(village_c)}" if village_c else None,
                f"Pincode {r['pincode']}" if r.get('pincode') else None,
                'Pricing not published in the registry — verify with the promoter.',
                'Plot layouts: confirm DTCP/CMDA approval and OSR compliance before buying.'
                if r.get('record_type') == 'layout' else None,
            ])),
            'last_checked': scraped.get('scraped_at'),
        }
        added.append(rec)
        by_rera[rera] = rec
        by_name.setdefault(name_key(name), rec)

    matched_loc = sum(1 for a in added if a['geo_precision'] == 'approximate')
    print(f'scraped: {len(scraped["projects"])}')
    print(f'  added:      {len(added)} new registry projects')
    print(f'  backfilled: {backfilled} RERA numbers onto curated records')
    print(f'  skipped:    {skipped}')
    print(f'  locality-matched: {matched_loc}/{len(added)} '
          f'({len(added) - matched_loc} placed at taluk/district centroid)')

    if args.dry_run:
        from collections import Counter
        print('  top unmatched localities:',
              Counter(a['locality'] for a in added if a['geo_precision'] != 'approximate').most_common(12))
        return

    projects.extend(added)
    projects.sort(key=lambda p: p['name'])
    with open(os.path.join(DATA, 'projects.json'), 'w', encoding='utf-8') as f:
        json.dump({'projects': projects}, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print(f'wrote projects.json ({len(projects)} total)')


if __name__ == '__main__':
    main()
