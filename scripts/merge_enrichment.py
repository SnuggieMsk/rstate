#!/usr/bin/env python3
"""Merge researched pricing/configuration data into docs/data/projects.json.

Registry-sourced projects arrive with no pricing (TNRERA does not publish it),
so this folds in price/ticket/configuration researched from developer sites and
property portals. Records are matched by the project `id`, never by name.

Input JSON: {"enrichment": [{"id": ..., "found": true, "price_sqft_min": ...}, ...]}
Anything with found:false or null fields is skipped rather than written as a gap.

Usage: python3 scripts/merge_enrichment.py <file.json> [<file2.json> ...] [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA = os.path.join(ROOT, 'docs', 'data')

# Numeric fields are only accepted as positive numbers; text fields as non-empty strings.
NUM_FIELDS = ('price_sqft_min', 'price_sqft_max', 'ticket_min_lakh', 'ticket_max_lakh',
              'unit_size_min_sqft', 'unit_size_max_sqft', 'total_units', 'land_area_acres')
TEXT_FIELDS = ('config_mix', 'dominant_config', 'density_note', 'expected_completion')
VALID_STAGES = {'pre-launch', 'new-launch', 'under-construction', 'nearing-possession', 'completed'}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    if not args:
        raise SystemExit(__doc__)

    with open(os.path.join(DATA, 'projects.json')) as f:
        pdata = json.load(f)
    by_id = {p['id']: p for p in pdata['projects']}

    records = []
    for path in args:
        with open(path) as f:
            records += json.load(f)['enrichment']

    applied, not_found, no_data, missing_id = 0, 0, 0, []
    priced = 0
    for r in records:
        p = by_id.get(r.get('id'))
        if p is None:
            missing_id.append(r.get('id'))
            continue
        if not r.get('found'):
            not_found += 1
            continue
        touched = False
        for f in NUM_FIELDS:
            v = r.get(f)
            if isinstance(v, (int, float)) and v > 0:
                p[f] = v
                touched = True
        for f in TEXT_FIELDS:
            v = r.get(f)
            if isinstance(v, str) and v.strip():
                p[f] = v.strip()
                touched = True
        if r.get('stage_observed') in VALID_STAGES:
            p['stage'] = r['stage_observed']
            touched = True
        for u in r.get('sources') or []:
            if isinstance(u, str) and u.startswith('http') and u not in p.get('sources', []):
                p.setdefault('sources', []).append(u)
                touched = True
        if r.get('notes'):
            note = r['notes'].strip()
            if note and note not in (p.get('notes') or ''):
                p['notes'] = ((p.get('notes') or '') + ' ' + note).strip()
                touched = True
        if touched:
            applied += 1
            # A record carrying real pricing is no longer registry-only.
            if p.get('price_sqft_min') or p.get('ticket_min_lakh'):
                p['source'] = 'curated'
                p['data_confidence'] = r.get('data_confidence') or 'reported'
                priced += 1
        else:
            no_data += 1

    print(f'enrichment records: {len(records)}')
    print(f'  applied:        {applied} ({priced} now carry pricing and are promoted to curated)')
    print(f'  research found nothing: {not_found}')
    print(f'  found but no usable fields: {no_data}')
    if missing_id:
        print(f'  UNKNOWN ids (skipped): {missing_id}')

    if dry:
        return
    with open(os.path.join(DATA, 'projects.json'), 'w', encoding='utf-8') as f:
        json.dump(pdata, f, indent=1, ensure_ascii=False)
        f.write('\n')
    total_priced = sum(1 for p in pdata['projects']
                       if p.get('price_sqft_min') or p.get('ticket_min_lakh'))
    print(f'wrote projects.json — {total_priced}/{len(pdata["projects"])} projects now have pricing')


if __name__ == '__main__':
    main()
