#!/usr/bin/env python3
"""Merge researched locality price bands into docs/data/localities.json.

A locality carries two independent bands. `price_band_*` is the built-up rate for
apartments; `plot_band_*` is the rate per sqft of land. They are not interchangeable,
and the Upside Score picks whichever matches the project's own product type.

Across the outer belt land runs well below built-up. In prime Chennai it inverts —
RA Puram land at 34,000/sqft against apartments at 22,500 — because scarce land
carries redevelopment FSI value. Both patterns are genuine; an inverted band in a
prime locality is not an error to fix.

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
import re
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
# A ceiling this far above the best comparable behind it is not measurement, it is
# extrapolation. Melavalam asserted 1,300 with nothing above 950 behind it.
CEILING_TOLERANCE = 1.15
# Below this many named comparables a band is one listing's opinion, not a market.
MIN_COMPARABLES = 2
# Chennai residential yields sit near 2-4%. 12.9% came from a developer's marketing
# blog and would read as measured fact in the UI.
MAX_PLAUSIBLE_YIELD = 8.0
# The CMA bounding box, same as scripts/merge_rera_csv.py. A locality geocoded
# outside it is a mangled registry string, not a micro-market.
LAT_RANGE, LNG_RANGE = (11.8, 14.2), (79.0, 80.9)
# Zone labels and unresolvable registry residue that must never become localities.
NOT_A_LOCALITY = {'west chennai', 'chennai', 'chennai district', 'ninnaijarai'}


def band_quality(lo, hi, comps):
    """Grade the evidence behind a band: 'comparables' or 'unverified'.

    An audit of the first research round found the striking "prime Chennai land
    trades above built-up" pattern was, in six of seven cases, a portal's summary
    series with not one recomputed transaction behind it. A band and a band-shaped
    quotation look identical in the data, so the difference is recorded explicitly
    and any estimate derived from a weak band says so.
    """
    rates = [c['rate_sqft'] for c in comps if c.get('rate_sqft')]
    if len(rates) < MIN_COMPARABLES:
        return 'unverified'
    if hi and hi > max(rates) * CEILING_TOLERANCE:
        return 'unverified'
    return 'comparables'


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


# Layout names in Chennai are highly generic — 215 registry records contain "Nagar".
# Stripping those tokens lets the same layout be recognised across two researchers'
# spellings ("Urban Tree Crystal Crown" vs "Crystal Crown by Urban Tree - Phase 2").
GENERIC_TOKENS = re.compile(
    r'\b(nagar|garden|gardens|avenue|city|phase|layout|sri|extension|annex|enclave|'
    r'township|estate|park|homes|plot|plots|the|and|of|i|ii|iii|iv|v|1|2|3|4|5)\b')
# Two records of the same layout, recomputed independently, land within a rounding
# error of each other. A wider gap means two different layouts sharing a stock name.
SAME_RATE_TOLERANCE = 0.02


def layout_key(name):
    t = GENERIC_TOKENS.sub(' ', (name or '').lower())
    t = re.sub(r'[^a-z0-9 ]', ' ', t)
    toks = sorted(x for x in t.split() if len(x) > 2)
    return ' '.join(toks) or (name or '').strip().lower()


def flag_contested(localities):
    """Mark comparables that two localities both claim, and return how many.

    Researchers working one locality each will each pull the same layout from a
    portal's neighbourhood-level listing page, so a band can look independently
    evidenced while resting on its neighbour's inventory. MGP Sanjanaa at 9,007
    was Thoraipakkam's only in-locality comparable and simultaneously Neelankarai's.

    A contested layout is not reassigned — we have no basis to pick a winner — it
    is excluded from the evidence count, so a band that only stood up because of
    borrowed inventory is re-graded 'unverified' rather than quietly kept.
    """
    seen = {}
    for l in localities:
        for c in l.get('plot_comparables') or []:
            c.pop('contested', None)
            if c.get('rate_sqft'):
                seen.setdefault(layout_key(c['layout']), []).append((l['name'], c))

    contested = 0
    for claims in seen.values():
        if len({name for name, _ in claims}) < 2:
            continue
        for i, (name_a, a) in enumerate(claims):
            for name_b, b in claims[i + 1:]:
                if name_a == name_b:
                    continue
                lo, hi = sorted((a['rate_sqft'], b['rate_sqft']))
                # Same name at a different rate is a different layout, not a duplicate.
                if lo and hi / lo <= 1 + SAME_RATE_TOLERANCE:
                    for c in (a, b):
                        if not c.get('contested'):
                            c['contested'] = True
                            contested += 1
    return contested


def regrade(localities):
    """Re-grade every plot band against its uncontested evidence."""
    changed = []
    for l in localities:
        if not l.get('plot_band_min'):
            continue
        comps = [c for c in (l.get('plot_comparables') or []) if not c.get('contested')]
        before = l.get('plot_band_quality')
        after = band_quality(l.get('plot_band_min'), l.get('plot_band_max'), comps)
        if after != before:
            l['plot_band_quality'] = after
            changed.append(f'{l["name"]}: {before} -> {after}')
    return changed


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
        if name.lower() in NOT_A_LOCALITY:
            rejected.append(f'{name}: a zone label or unresolvable registry string, not a locality')
            continue
        if r.get('lat') is not None and not (
                LAT_RANGE[0] <= r['lat'] <= LAT_RANGE[1]
                and LNG_RANGE[0] <= (r.get('lng') or 0) <= LNG_RANGE[1]):
            rejected.append(f'{name}: geocoded {r["lat"]},{r.get("lng")} — outside the CMA')
            continue
        if (r.get('rental_yield_pct') or 0) > MAX_PLAUSIBLE_YIELD:
            rejected.append(f'{name}: rental yield {r["rental_yield_pct"]}% is not credible — dropped')
            r['rental_yield_pct'] = None

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
        #
        # Only re-grade when THIS record actually carries plot research. Grading on every
        # incoming record meant a one-field trend update silently downgraded a locality's
        # evidence — Sholinganallur's band, built from 51 named comparables, flipped to
        # "unverified" and pushed the weak-estimate caveat onto three more projects.
        if r.get('plot_band_min') or comps:
            l['plot_band_quality'] = band_quality(
                r.get('plot_band_min'), r.get('plot_band_max'), comps)
        # The apartment band has no comparables array to check, so it is graded on
        # whether the researcher recorded where the figure came from.
        if r.get('price_band_min'):
            note = (r.get('price_band_note') or '').lower()
            l['price_band_quality'] = 'unverified' if (
                'not recomputed' in note or 'reported only' in note or not note
            ) else 'comparables'
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

    n_contested = flag_contested(ldata['localities'])
    regraded = regrade(ldata['localities'])
    print(f'\n  comparables claimed by two localities at the same rate: {n_contested}')
    if regraded:
        print(f'  {len(regraded)} bands re-graded once borrowed evidence was excluded:')
        for x in regraded:
            print('    ' + x)

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
