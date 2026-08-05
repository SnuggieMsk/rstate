#!/usr/bin/env python3
"""Merge official TNRERA CSV exports into docs/data/projects.json.

Download from the official portal (one file per type and year):
  Buildings: https://rera.tn.gov.in/registered-building/tn
  Layouts:   https://rera.tn.gov.in/registered-layout/tn

This is the only source that is genuinely *official*, so a record matched here
is upgraded to data_confidence="verified". It also carries three things the
third-party mirror does not:
  * exact site latitude/longitude (geo_precision becomes "exact")
  * the official project completion date, including later revisions
  * registration status changes — cancellations and revised registrations

Usage: python3 scripts/merge_rera_csv.py <export.csv> [more.csv ...] [--dry-run]
"""
import argparse
import csv
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA = os.path.join(ROOT, 'docs', 'data')
CMA_DISTRICTS = {'1': 'Kancheepuram', '2': 'Tiruvallur', '29': 'Chennai', '35': 'Chengalpattu'}
DISTRICT_CENTROIDS = {'1': (12.834, 79.704), '2': (13.143, 79.909),
                      '29': (13.070, 80.240), '35': (12.682, 79.986)}

REG_RE = re.compile(r'(TNRERA/(\d+)/([A-Z]+)/(\d+)/(\d+))')
COORD_RE = re.compile(r'Latitude\s*[-:]\s*([\d.]+)\s*;?\s*Longitude\s*[-:]\s*([\d.]+)', re.I)

NAME_RE = re.compile(r'Project Name\s*:\s*(.+?)(?:Registration of|Proposed|Construction of|$)', re.S)
UNITS_RE = re.compile(r'(\d{1,4})\s*(?:Dwelling|dwelling|residential)\s*units?')
DATE_RE = re.compile(r'(\d{2})[.\-/](\d{2})[.\-/](\d{4})')

# The CMA sits inside this box. Anything outside it is a mis-keyed filing, not a site.
LAT_RANGE, LNG_RANGE = (11.8, 14.2), (79.0, 80.9)


def in_cma(lat, lng):
    return (lat is not None and lng is not None
            and LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LNG_RANGE[0] <= lng <= LNG_RANGE[1])


def norm_reg(s):
    return (s or '').upper().replace('TN/', 'TNRERA/').replace('/BUILDING/', '/BLG/').replace('/LAYOUT/', '/LO/')


def iso_date(s):
    m = DATE_RE.search(s or '')
    return f'{m.group(3)}-{m.group(2)}-{m.group(1)}' if m else None


def _candidates(v):
    """Yield the plausible readings of one raw coordinate figure.

    Promoters key coordinates into a free-text field, so a single export mixes
    at least three notations for the same thing:
      13.0574      plain decimal degrees
      130342.5     packed DDMMSS.s  (13 deg 03 min 42.5 sec)
      1305741      decimal degrees with the point dropped
    """
    yield v
    if v > 100:                                    # packed DDMMSS[.s]
        whole = int(v)
        deg, rest = divmod(whole, 10000)
        mins, secs = divmod(rest, 100)
        if mins < 60 and secs < 60:
            yield deg + mins / 60 + (secs + v - whole) / 3600
    scaled = v                                     # misplaced decimal point
    for _ in range(8):
        scaled /= 10
        yield scaled


def parse_coords(text):
    """Return (lat, lng) inside the CMA, or None if the filing cannot be read.

    Tries each notation for both figures, and accepts a lat/lng swap — some
    filings label the columns the wrong way round. A reading is only used when
    exactly one interpretation lands inside the metropolitan area, so an
    ambiguous figure falls back to the locality centroid rather than guessing.
    """
    m = COORD_RE.search(text or '')
    if not m:
        return None
    try:
        a, b = float(m.group(1)), float(m.group(2))
    except ValueError:
        return None
    hits = set()
    for lat_raw, lng_raw in ((a, b), (b, a)):
        for lat in _candidates(lat_raw):
            if not LAT_RANGE[0] <= lat <= LAT_RANGE[1]:
                continue
            for lng in _candidates(lng_raw):
                if LNG_RANGE[0] <= lng <= LNG_RANGE[1]:
                    hits.add((round(lat, 6), round(lng, 6)))
    return hits.pop() if len(hits) == 1 else None


def parse_csv(path):
    out = []
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        for row in csv.DictReader(f):
            cell = lambda k: (row.get(k) or '').strip()
            m = REG_RE.match(cell('Project Registration No.'))
            if not m:
                continue
            details = cell('Project Details and Address')
            other = cell('Other Details')
            coords = parse_coords(other) or parse_coords(details)
            name = NAME_RE.search(details)
            units = [int(u) for u in UNITS_RE.findall(details)]
            out.append({
                'reg': m.group(1), 'district_code': m.group(2),
                'lat': coords[0] if coords else None,
                'lng': coords[1] if coords else None,
                'name': name.group(1).strip()[:80] if name else None,
                'total_units': max(units) if units else None,
                'completion': iso_date(cell('Project Completion Date')),
                'status_note': cell('Current Status of the Project'),
                'promoter': cell('Name and Address of the Promoter').split(',')[0].strip() or None,
            })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    rows = []
    for p in args.files:
        got = parse_csv(p)
        print(f'{os.path.basename(p)}: {len(got)} rows')
        rows += got
    cma = [r for r in rows if r['district_code'] in CMA_DISTRICTS]
    print(f'total {len(rows)} rows, {len(cma)} in the 4 CMA districts')

    with open(os.path.join(DATA, 'projects.json')) as f:
        pdata = json.load(f)
    with open(os.path.join(DATA, 'localities.json')) as f:
        centroids = {l['name'].lower(): (l['lat'], l['lng'])
                     for l in json.load(f)['localities'] if l.get('lat')}
    by_reg = {norm_reg(p.get('rera_no')): p for p in pdata['projects'] if p.get('rera_no')}

    verified = coords_set = completion_set = units_set = cancelled = revised = demoted = 0
    unmatched = []
    superseded = 0
    for r in cma:
        p = by_reg.get(norm_reg(r['reg']))
        if p is None:
            # A cancelled registration re-issued under a new number is not a gap —
            # the live registry (and the mirror) correctly shows only the successor.
            succ = REG_RE.search(r['status_note'] or '')
            target = by_reg.get(norm_reg(succ.group(1))) if succ else None
            if target is not None and 'cancel' in (r['status_note'] or '').lower():
                target['registration_status'] = (
                    f'Supersedes {r["reg"]}, whose registration was cancelled and re-issued under '
                    f'this number (per official TNRERA export).')
                superseded += 1
            else:
                unmatched.append(r)
            continue
        # Official source: this record is now verifiable against the portal itself.
        p['data_confidence'] = 'verified'
        p['rera_verified_on'] = 'official TNRERA export'
        verified += 1
        if r['lat'] and r['lng']:
            p['lat'], p['lng'] = r['lat'], r['lng']
            p['geo_precision'] = 'exact'
            coords_set += 1
        elif not in_cma(p.get('lat'), p.get('lng')):
            # An earlier run trusted the raw figure and dropped the pin in the
            # Bay of Bengal (or New York). Fall back to the locality centroid so
            # the map stays honest about how precisely the site is known.
            pt = centroids.get((p.get('locality') or '').lower())
            p['lat'], p['lng'] = pt or DISTRICT_CENTROIDS[r['district_code']]
            p['geo_precision'] = 'locality' if pt else 'district'
            demoted += 1
        if r['completion']:
            p['expected_completion'] = r['completion']
            completion_set += 1
        if r['total_units'] and not p.get('total_units'):
            p['total_units'] = r['total_units']
            units_set += 1
        note = r['status_note']
        if note:
            low = note.lower()
            if 'cancel' in low:
                p['status'] = 'withdrawn'
                p['registration_status'] = note[:200]
                cancelled += 1
            elif 'revis' in low:
                p['registration_status'] = note[:200]
                revised += 1

    print(f'\n  verified against official export: {verified}')
    print(f'  exact coordinates applied:        {coords_set}')
    print(f'  unreadable coords -> locality centroid: {demoted}')
    print(f'  completion dates applied:         {completion_set}')
    print(f'  unit counts backfilled:           {units_set}')
    print(f'  registrations CANCELLED (-> withdrawn): {cancelled}')
    print(f'  registrations revised (noted):    {revised}')
    print(f'  cancelled + re-issued (noted on successor): {superseded}')
    print(f'  in export but not yet tracked:    {len(unmatched)}')
    for r in unmatched[:10]:
        print(f'      {r["reg"]}  {str(r["name"])[:52]}')

    if args.dry_run:
        return
    with open(os.path.join(DATA, 'projects.json'), 'w', encoding='utf-8') as f:
        json.dump(pdata, f, indent=1, ensure_ascii=False)
        f.write('\n')
    tot = sum(1 for p in pdata['projects'] if p.get('data_confidence') == 'verified')
    print(f'\nwrote projects.json — {tot} records now officially verified')


if __name__ == '__main__':
    main()
