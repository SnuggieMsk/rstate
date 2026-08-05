#!/usr/bin/env python3
"""Derive locality-benchmark price estimates for projects that have no published price.

TNRERA registers a project but never publishes what it sells for, and for plotted
layouts the portals and the registry list almost disjoint sets of projects — a name
lookup fails roughly 97% of the time. So most registry records will never have a
researched price, and the only defensible thing to say about them is what land or
built-up area costs in that locality.

That estimate is kept in its OWN fields. It never touches price_sqft_min /
ticket_min_lakh, which mean "somebody published this number for this specific
project". Two reasons that separation matters:

  * Honesty. A derived figure displayed in the same field as a researched one is
    indistinguishable to the reader, and this dataset is used to make crore-scale
    decisions.
  * Circularity. The Upside Score's relative_pricing factor asks "is this project
    cheap for its locality?". Answering it with the locality band itself would score
    every estimated project as exactly average while looking like real signal.

Estimates DO feed segment_fit, so the persona lenses can place a project in a client
bracket — that is a judgement about which buyer it suits, not a claim about its price.

Usage: python3 scripts/estimate_prices.py [--dry-run]
"""
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
DATA = os.path.join(ROOT, 'docs', 'data')
RETIRED = {'withdrawn', 'superseded', 'unverified'}

# Fallbacks when a locality has no researched typical size. Deliberately conservative:
# a wrong size makes the ticket estimate wrong even when the rate is right.
DEFAULT_PLOT_SQFT = 1200
DEFAULT_FLAT_SQFT = 1050

# Estimating a corridor-wide rate is already a stretch; below this many localities
# contributing a band, a corridor median is not worth publishing.
MIN_CORRIDOR_SAMPLE = 3


def band_for(p, loc):
    """Return (lo, hi, typical_size, basis) for the project's own product type."""
    if p.get('type') == 'plotted':
        return (loc.get('plot_band_min'), loc.get('plot_band_max'),
                loc.get('typical_plot_size_sqft') or DEFAULT_PLOT_SQFT, 'land')
    return (loc.get('price_band_min'), loc.get('price_band_max'),
            loc.get('typical_flat_size_sqft') or DEFAULT_FLAT_SQFT, 'built-up')


def corridor_bands(localities):
    """Median plot and apartment band per corridor, for localities we never researched.

    A corridor spans very different micro-markets, so this is the weakest rung on the
    ladder and is labelled as such — it exists so a project is not simply blank.
    """
    buckets = {}
    for l in localities:
        c = l.get('corridor')
        if not c:
            continue
        b = buckets.setdefault(c, {'plot': [], 'flat': [], 'psize': [], 'fsize': []})
        if l.get('plot_band_min') and l.get('plot_band_max'):
            b['plot'].append((l['plot_band_min'], l['plot_band_max']))
        if l.get('price_band_min') and l.get('price_band_max'):
            b['flat'].append((l['price_band_min'], l['price_band_max']))
        if l.get('typical_plot_size_sqft'):
            b['psize'].append(l['typical_plot_size_sqft'])
        if l.get('typical_flat_size_sqft'):
            b['fsize'].append(l['typical_flat_size_sqft'])

    def med(xs):
        return sorted(xs)[len(xs) // 2] if xs else None

    out = {}
    for c, b in buckets.items():
        e = {}
        for key in ('plot', 'flat'):
            if len(b[key]) >= MIN_CORRIDOR_SAMPLE:
                e[key] = (med([x[0] for x in b[key]]), med([x[1] for x in b[key]]),
                          len(b[key]))
        e['psize'], e['fsize'] = med(b['psize']), med(b['fsize'])
        out[c] = e
    return out


def clear_estimate(p):
    for f in ('est_price_sqft_min', 'est_price_sqft_max', 'est_ticket_min_lakh',
              'est_ticket_max_lakh', 'est_basis', 'est_source', 'est_weak'):
        p.pop(f, None)


def main():
    dry = '--dry-run' in sys.argv
    with open(os.path.join(DATA, 'projects.json')) as f:
        pdata = json.load(f)
    with open(os.path.join(DATA, 'localities.json')) as f:
        localities = json.load(f)['localities']
    by_name = {l['name'].lower(): l for l in localities}
    by_corridor = corridor_bands(localities)

    from_locality = from_corridor = skipped_priced = no_band = not_for_sale = 0
    for p in pdata['projects']:
        clear_estimate(p)
        if p.get('status') in RETIRED:
            continue
        if p.get('price_sqft_min') or p.get('ticket_min_lakh'):
            skipped_priced += 1
            continue
        # Government rehabilitation tenements are allotted, not sold. Attaching a
        # market-derived ticket to one would invent a price that cannot exist.
        if p.get('not_for_sale'):
            not_for_sale += 1
            continue

        loc = by_name.get((p.get('locality') or '').lower())
        lo = hi = None
        if loc:
            lo, hi, size, basis = band_for(p, loc)
            src, tier = loc['name'], 'locality'
        if lo is None or hi is None:
            e = by_corridor.get(p.get('corridor')) or {}
            key = 'plot' if p.get('type') == 'plotted' else 'flat'
            if key in e:
                lo, hi, n = e[key]
                size = (e['psize'] if key == 'plot' else e['fsize']) or \
                    (DEFAULT_PLOT_SQFT if key == 'plot' else DEFAULT_FLAT_SQFT)
                basis = 'land' if key == 'plot' else 'built-up'
                src, tier = f"{p['corridor']} corridor median of {n} localities", 'corridor'
            else:
                no_band += 1
                continue

        p['est_price_sqft_min'], p['est_price_sqft_max'] = lo, hi
        p['est_ticket_min_lakh'] = round(lo * size / 1e5, 1)
        p['est_ticket_max_lakh'] = round(hi * size / 1e5, 1)
        p['est_basis'] = (f'{basis} rate for {src}, applied to a typical '
                          f'{int(size):,} sqft {"plot" if basis == "land" else "unit"}')
        if basis == 'land' and (loc or {}).get('plot_band_quality') == 'unverified':
            p['est_basis'] += (' — that land band was quoted from a portal summary rather '
                               'than rebuilt from named comparables, so treat it as weak')
            p['est_weak'] = True
        p['est_source'] = tier
        if tier == 'locality':
            from_locality += 1
        else:
            from_corridor += 1

    print(f'already priced (left alone):      {skipped_priced}')
    print(f'estimated from its own locality:  {from_locality}')
    print(f'estimated from a corridor median: {from_corridor}')
    print(f'not for sale (govt housing):      {not_for_sale}')
    print(f'no band available, left blank:    {no_band}')

    if dry:
        return
    with open(os.path.join(DATA, 'projects.json'), 'w', encoding='utf-8') as f:
        json.dump(pdata, f, indent=1, ensure_ascii=False)
        f.write('\n')
    tot = sum(1 for p in pdata['projects']
              if p.get('price_sqft_min') or p.get('ticket_min_lakh') or p.get('est_ticket_min_lakh'))
    print(f'\nwrote projects.json — {tot}/{len(pdata["projects"])} projects now carry a '
          f'price or a price estimate')


if __name__ == '__main__':
    main()
