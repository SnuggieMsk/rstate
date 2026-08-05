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

REG_RE = re.compile(r'(TNRERA/(\d+)/([A-Z]+)/(\d+)/(\d+))')
COORD_RE = re.compile(r'Latitude\s*[-:]\s*([\d.]+)\s*;?\s*Longitude\s*[-:]\s*([\d.]+)', re.I)
NAME_RE = re.compile(r'Project Name\s*:\s*(.+?)(?:Registration of|Proposed|Construction of|$)', re.S)
UNITS_RE = re.compile(r'(\d{1,4})\s*(?:Dwelling|dwelling|residential)\s*units?')
DATE_RE = re.compile(r'(\d{2})[.\-/](\d{2})[.\-/](\d{4})')


def norm_reg(s):
    return (s or '').upper().replace('TN/', 'TNRERA/').replace('/BUILDING/', '/BLG/').replace('/LAYOUT/', '/LO/')


def iso_date(s):
    m = DATE_RE.search(s or '')
    return f'{m.group(3)}-{m.group(2)}-{m.group(1)}' if m else None


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
            coords = COORD_RE.search(other) or COORD_RE.search(details)
            name = NAME_RE.search(details)
            units = [int(u) for u in UNITS_RE.findall(details)]
            out.append({
                'reg': m.group(1), 'district_code': m.group(2),
                'lat': float(coords.group(1)) if coords else None,
                'lng': float(coords.group(2)) if coords else None,
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
    by_reg = {norm_reg(p.get('rera_no')): p for p in pdata['projects'] if p.get('rera_no')}

    verified = coords_set = completion_set = units_set = cancelled = revised = 0
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
