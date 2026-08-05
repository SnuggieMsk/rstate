#!/usr/bin/env python3
"""Merge researched locality price bands into docs/data/localities.json.

A locality carries two independent bands. `price_band_*` is the built-up rate for
apartments; `plot_band_*` is the rate per sqft of land. They are not interchangeable
— land typically costs about a third of built-up area in the same Chennai locality —
and the Upside Score picks whichever matches the project's own product type.

Earlier research predated that split and recorded a single `price_band`, sometimes
filled with a land rate for outer localities that have no apartment market at all.
Researchers are asked to audit that field; where they report it was really a land
rate, this script moves it to `plot_band_*` rather than leaving it to be compared
against apartments.

Input JSON: {"localities": [{"name": ..., "found": true, "plot_band_min": ...}, ...]}
Usage: python3 scripts/merge_locality_bands.py <file.json> [more.json ...] [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA = os.path.join(ROOT, 'docs', 'data')

NUM_FIELDS = ('plot_band_min', 'plot_band_max', 'price_band_min', 'price_band_max',
              'typical_plot_size_sqft', 'typical_flat_size_sqft', 'rental_yield_pct',
              'lat', 'lng')
TEXT_FIELDS = ('plot_band_note', 'price_band_note', 'trend', 'trend_note', 'corridor',
               'rate_basis', 'data_confidence')
# `tier` is computed by score.py from the band ceiling and must never be written here.
COMPUTED = {'tier'}

# A band whose ceiling is more than this multiple of its floor carries no information.
MAX_BAND_SPREAD = 4.0


def bad_band(lo, hi):
    if lo is None or hi is None:
        return None
    if lo <= 0 or hi <= 0:
        return 'non-positive'
    if hi < lo:
        return 'max below min'
    if hi / lo > MAX_BAND_SPREAD:
        return f'spread {hi / lo:.1f}x — too wide to be useful'
    return None


def main():
    paths = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    if not paths:
        raise SystemExit(__doc__)

    with open(os.path.join(DATA, 'localities.json')) as f:
        ldata = json.load(f)
    by_name = {l['name'].lower(): l for l in ldata['localities']}

    records = []
    for p in paths:
        with open(p) as f:
            records += json.load(f)['localities']

    created = updated = not_found = plot_bands = reclassified = 0
    rejected, audits = [], []
    for r in records:
        name = (r.get('name') or '').strip()
        if not name:
            continue
        if not r.get('found'):
            not_found += 1
            continue

        for lo_f, hi_f in (('plot_band_min', 'plot_band_max'),
                           ('price_band_min', 'price_band_max')):
            why = bad_band(r.get(lo_f), r.get(hi_f))
            if why:
                rejected.append(f'{name}: {lo_f[:-4]} {r[lo_f]}-{r[hi_f]} rejected ({why})')
                r[lo_f] = r[hi_f] = None

        l = by_name.get(name.lower())
        if l is None:
            l = {'name': name, 'sources': [], 'segment_fit': [], 'flood_risk': 'unknown'}
            ldata['localities'].append(l)
            by_name[name.lower()] = l
            created += 1
        else:
            updated += 1

        # The existing single band was really a land rate: move it where it belongs
        # rather than leave it to be compared against apartment pricing.
        audit = (r.get('band_audit') or '').lower()
        if audit:
            audits.append(f'{name}: {r["band_audit"]}')
        if ('land' in audit and 'apartment' not in audit.split('land')[0][-40:]
                and l.get('price_band_min') and not r.get('plot_band_min')
                and r.get('has_apartment_market') is False):
            l['plot_band_min'], l['plot_band_max'] = l['price_band_min'], l['price_band_max']
            l['price_band_min'] = l['price_band_max'] = None
            l['plot_band_note'] = ('Reclassified: this figure was recorded as an apartment '
                                   'band but measures land. ' + (l.get('price_note') or ''))[:400]
            reclassified += 1

        for f in NUM_FIELDS:
            v = r.get(f)
            if isinstance(v, (int, float)) and v > 0:
                l[f] = v
        for f in TEXT_FIELDS:
            v = r.get(f)
            if isinstance(v, str) and v.strip():
                l[f] = v.strip()
        if isinstance(r.get('has_apartment_market'), bool):
            l['has_apartment_market'] = r['has_apartment_market']
            if r['has_apartment_market'] is False:
                l['price_band_min'] = l['price_band_max'] = None
        if r.get('segment_fit'):
            l['segment_fit'] = sorted({s.lower() for s in r['segment_fit']
                                       if s.lower() in ('boardroom', 'executive', 'value')})
        for u in r.get('sources') or []:
            if isinstance(u, str) and u.startswith('http') and u not in l.setdefault('sources', []):
                l['sources'].append(u)
        comps = [c for c in (r.get('plot_comparables') or []) if c.get('rate_sqft')]
        if comps:
            l['plot_comparables'] = comps
        # A band built from named comparables the researcher recomputed themselves is a
        # different thing from one quoted wholesale off a portal's summary page. Record
        # which it is so an estimate derived from it can carry the caveat.
        if l.get('plot_band_min'):
            l['plot_band_quality'] = 'comparables' if comps else 'unverified'
        for f in COMPUTED:
            l.pop(f, None)
        if l.get('plot_band_min'):
            plot_bands += 1

    print(f'locality records in:        {len(records)}')
    print(f'  created:                  {created}')
    print(f'  updated:                  {updated}')
    print(f'  research found nothing:   {not_found}')
    print(f'  now carry a plot band:    {plot_bands}')
    print(f'  single band reclassified as land: {reclassified}')
    if rejected:
        print(f'\n  {len(rejected)} bands REJECTED as unusable:')
        for x in rejected:
            print('    ' + x)
    if audits:
        print(f'\n  {len(audits)} audit notes on pre-existing bands:')
        for x in audits[:40]:
            print('    ' + x[:160])

    if dry:
        return
    with open(os.path.join(DATA, 'localities.json'), 'w', encoding='utf-8') as f:
        json.dump(ldata, f, indent=1, ensure_ascii=False)
        f.write('\n')
    tot = len(ldata['localities'])
    withplot = sum(1 for l in ldata['localities'] if l.get('plot_band_min'))
    withflat = sum(1 for l in ldata['localities'] if l.get('price_band_min'))
    print(f'\nwrote localities.json — {tot} localities, {withplot} with a plot band, '
          f'{withflat} with an apartment band')


if __name__ == '__main__':
    main()
