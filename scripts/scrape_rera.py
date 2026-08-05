#!/usr/bin/env python3
"""Scrape the public TNRERA registration index (via the Proquiro mirror) for
Chennai Metropolitan Area projects.

The official portal (rera.tn.gov.in) returns HTTP 503 to automated access and is
additionally blocked by web-unlocker policy as a government domain, so this reads
a public third-party mirror of the same registry. Records produced here are
therefore marked data_confidence="reported" (mirror-sourced), never "verified".

Requires BRIGHTDATA_API_KEY in the environment (the mirror 403s direct requests).
Pages are cached under .cache/rera/ so re-runs are cheap and reviewable.

Usage:
    export BRIGHTDATA_API_KEY=...
    python3 scripts/scrape_rera.py            # scrape + write scratch JSON
    python3 scripts/scrape_rera.py --limit 20 # smoke test
"""
import argparse
import concurrent.futures as cf
import html
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CACHE = os.path.join(ROOT, '.cache', 'rera')
OUT = os.path.join(ROOT, '.cache', 'rera_scraped.json')
BASE = 'https://proquiro.com/tools/rera-tamil-nadu/buildings/'

# TNRERA district codes that make up the Chennai Metropolitan Area / commuter belt.
CMA_DISTRICTS = {'1': 'Kancheepuram', '2': 'Tiruvallur', '29': 'Chennai', '35': 'Chengalpattu'}


def fetch(url, cache_key, retries=3):
    """Fetch through the Bright Data unlocker, with an on-disk cache."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, cache_key + '.html')
    if os.path.exists(path) and os.path.getsize(path) > 5000:
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read()
    key = os.environ.get('BRIGHTDATA_API_KEY')
    if not key:
        raise SystemExit('BRIGHTDATA_API_KEY not set in environment')
    payload = json.dumps({'zone': 'cli_unlocker', 'url': url, 'format': 'raw'})
    for attempt in range(retries):
        try:
            res = subprocess.run(
                ['curl', '-sS', '-X', 'POST', 'https://api.brightdata.com/request',
                 '-H', f'Authorization: Bearer {key}',
                 '-H', 'Content-Type: application/json',
                 '--max-time', '90', '-d', payload],
                capture_output=True, text=True, timeout=120)
            body = res.stdout
            if len(body) > 5000:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(body)
                return body
        except subprocess.TimeoutExpired:
            pass
        time.sleep(1.5 * (attempt + 1))
    return ''


def strip_tags(h):
    h = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h, flags=re.S)
    t = html.unescape(re.sub(r'<[^>]+>', '|', h))
    t = re.sub(r'\|{2,}', '|', t)
    return re.sub(r'[ \t]+', ' ', t)


def parse_index(page_html):
    """Each table row is: name | promoter | type | year | status | RERA no."""
    rows = []
    # The row link lives in the <tr> opening tag as data-href, so match the whole element.
    for m in re.finditer(r'<tr[^>]*>.*?</tr>', page_html, flags=re.S):
        row = m.group(0)
        link = re.search(r'buildings/(tnrera-\d+-blg-\d+-\d+)/([a-z0-9\-]+)', row)
        if not link:
            continue
        cells = [re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', c))).strip()
                 for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, flags=re.S)]
        cells = [c for c in cells if c]
        slug_no, slug_name = link.group(1), link.group(2)
        parts = slug_no.split('-')  # tnrera-29-blg-0270-2025
        rera_no = f'TNRERA/{parts[1]}/BLG/{parts[3]}/{parts[4]}'
        rec = {
            'rera_no': rera_no, 'district_code': parts[1], 'reg_year': parts[4],
            'slug': f'{slug_no}/{slug_name}',
            'url': f'{BASE}{slug_no}/{slug_name}',
        }
        # cells order varies slightly; pick by shape
        text_cells = [c for c in cells if not c.startswith('TNRERA')]
        if text_cells:
            rec['name'] = text_cells[0]
        if len(text_cells) > 1:
            rec['promoter'] = text_cells[1]
        for c in cells:
            lc = c.lower()
            if lc in ('apartment', 'villa', 'plotted', 'commercial', 'mixed', 'row house'):
                rec['type'] = 'apartment' if lc == 'apartment' else lc
            elif lc in ('under construction', 'completed', 'new', 'ongoing'):
                rec['status_raw'] = c
            elif re.fullmatch(r'20\d\d', c):
                rec['reg_year'] = c
        rows.append(rec)
    # dedupe by rera_no, keep first
    seen, out = set(), []
    for r in rows:
        if r['rera_no'] in seen:
            continue
        seen.add(r['rera_no'])
        out.append(r)
    return out


# Address fields appear as "Label : value," but not every project publishes every
# field and the order varies, so each label is matched independently.
ADDR_FIELDS = {
    'village': r'Village\s*:\s*([^,|]{2,60})',
    'city': r'City/Town\s*:\s*([^,|]{2,60})',
    'taluk': r'Taluk\s*:\s*([^,|]{2,60})',
    'district': r'District\s*:\s*([^,|.]{2,40})',
    'pincode': r'Pincode\s*:?\s*(\d{6})',
    'survey': r'Survey No\s*:\s*([^|]{2,120}?),\s*(?:Village|City/Town|Taluk|District)',
}


def parse_detail(page_html):
    t = strip_tags(page_html)
    out = {}
    # The promoter's own address block also contains District/City, so prefer the
    # project-address block that follows "Survey No".
    anchor = t.find('Survey No')
    scope = t[anchor:anchor + 600] if anchor != -1 else t
    for key, pat in ADDR_FIELDS.items():
        m = re.search(pat, scope, re.I) or re.search(pat, t, re.I)
        if m:
            v = m.group(1).strip().strip('&.').strip()
            if v and v.lower() not in ('na', 'n/a', '-'):
                out[key] = v
    m = re.search(r'Builder / Developer\s*\|\s*([^|]{3,160})', t)
    if m:
        out['promoter_legal'] = m.group(1).strip()
    m = re.search(r'(?:Proposed date of completion|Completion date)\s*\|\s*([0-9]{2}[-/][0-9]{2}[-/][0-9]{4})', t, re.I)
    if m:
        out['completion_raw'] = m.group(1)
    m = re.search(r'(?:Total number of (?:units|apartments)|No\. of units)\s*\|\s*(\d{1,5})', t, re.I)
    if m:
        out['total_units'] = int(m.group(1))
    m = re.search(r'(?:Project cost|Total project cost)\s*\|\s*[₹Rs. ]*([\d,]+(?:\.\d+)?)\s*(crore|lakh)?', t, re.I)
    if m:
        try:
            val = float(m.group(1).replace(',', ''))
            unit = (m.group(2) or '').lower()
            out['project_cost_inr'] = int(val * (1e7 if unit == 'crore' else 1e5 if unit == 'lakh' else 1))
        except ValueError:
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0, help='cap detail fetches (smoke test)')
    ap.add_argument('--workers', type=int, default=8)
    args = ap.parse_args()

    print('Fetching TNRERA index …', flush=True)
    index_html = fetch(BASE + '?page=2', 'index')
    if not index_html:
        raise SystemExit('could not fetch index')
    rows = parse_index(index_html)
    print(f'  index rows: {len(rows)}')

    cma = [r for r in rows if r['district_code'] in CMA_DISTRICTS]
    print(f'  Chennai-metro rows: {len(cma)} '
          f'({", ".join(sorted(set(CMA_DISTRICTS[r["district_code"]] for r in cma)))})')
    if args.limit:
        cma = cma[:args.limit]

    print(f'Fetching {len(cma)} detail pages with {args.workers} workers …', flush=True)
    done = [0]

    def work(r):
        h = fetch(r['url'], r['slug'].replace('/', '__'))
        if h:
            r.update(parse_detail(h))
        done[0] += 1
        if done[0] % 25 == 0:
            print(f'  {done[0]}/{len(cma)}', flush=True)
        return r

    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        cma = list(ex.map(work, cma))

    got_village = sum(1 for r in cma if r.get('village'))
    print(f'  detail parsed: {got_village}/{len(cma)} with village/taluk')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump({'scraped_at': time.strftime('%Y-%m-%d'), 'source': BASE,
                   'projects': cma}, f, indent=1, ensure_ascii=False)
    print(f'wrote {OUT} ({len(cma)} records)')


if __name__ == '__main__':
    main()
