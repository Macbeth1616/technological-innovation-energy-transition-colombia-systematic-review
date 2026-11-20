"""Regenerate review/synthesis/evidence/results.json from the review records.

Run from the repo root, after build_summaries.py, build_tables.py and `review_cli.py biblio`
(it reads review/synthesis/tables/*.csv, rq1-scientometrics.json and the rq2/gN-table.json files):

    python3 review/synthesis/build_results_evidence.py [--out PATH] [--template PATH] [--old-set]

The record ids, regimes, sources and caption/label fields come from the template (default: the
current results.json); every count and cite list is recomputed for the included set
(included_ids.included()). rq2 records are built from rq2/gN-table.json with however many rows
those files hold. A record whose count becomes 0 is dropped and reported on stderr.
--old-set reproduces the pre-E8 set (extraction minus non-E8 full-text exclusions), for regression
testing of the templates against an older results.json.
"""
import argparse, collections, csv, itertools, json, re, sys
sys.path.insert(0, 'review/synthesis')
R = 'review/'; S = 'review/synthesis/'

ap_ = argparse.ArgumentParser()
ap_.add_argument('--out', default=S + 'evidence/results.json')
ap_.add_argument('--template', default=S + 'evidence/results.json')
ap_.add_argument('--old-set', action='store_true')
args = ap_.parse_args()

jl = lambda p: [json.loads(l) for l in open(p)]
if args.old_set:
    ex_ids = {r['record_id'] for r in jl(R + 'extraction.jsonl')}
    last = {}
    for r in jl(R + 'screening.jsonl'):
        if r['stage'] == 'ft' and r.get('final'): last[r['record_id']] = (r['decision'], r.get('reason'))
    ids = sorted(i for i in ex_ids if last.get(i, ('include',))[0] == 'include' or last[i][1] == 'E8')
else:
    from included_ids import included
    ids = included()
INC = set(ids)
rec = {r['id']: r for r in jl(R + 'records.jsonl')}
ex = {r['record_id']: r for r in jl(R + 'extraction.jsonl')}
tech = lambda rid: ex[rid]['data']['technology']['value']

G = {'Renewable generation (solar, wind, hydro, geothermal, ocean)': ['solar', 'wind', 'hydropower', 'geothermal', 'ocean-energy'],
     'Bioenergy': ['biomass-bioenergy'],
     'Grids, microgrids and storage': ['smart-grids-digitalization', 'microgrids-off-grid', 'energy-storage'],
     'Demand side (efficiency, electromobility)': ['energy-efficiency', 'electromobility'],
     'Low-carbon fuels (hydrogen, CCS, nuclear)': ['hydrogen-low-carbon-fuels', 'carbon-capture-storage', 'nuclear'],
     'System-level planning and other': ['multiple-or-system-level', 'other']}
grp = {t: g for g, ts in G.items() for t in ts}
SHORT = dict(zip(G, ['Renewables', 'Bioenergy', 'Grids/storage', 'Demand side', 'Low-carbon fuels', 'System-level']))
LONG = {v: k for k, v in SHORT.items()}
gof = lambda rid: grp[tech(rid)]
cite = lambda xs: '\\cite{' + ','.join(sorted(xs)) + '}'

dropped = []
def by_group(studies):
    """'Group: n \\cite{..}; ...' ordered by count desc, ties by first appearance in record-id order."""
    cnt = collections.Counter(gof(x) for x in sorted(studies))
    return '; '.join('%s: %d %s' % (g, n, cite({x for x in studies if gof(x) == g})) for g, n in cnt.most_common())

def first_items(entries, with_dir=False, n=6):
    """Verbatim example items: the first n (record id order, then item order) as in the coded files."""
    out = []
    for rid, x in entries[:n]:
        out.append('"%s" %s[%s]' % (x['item'], '(%s) ' % x['direction'] if with_dir else '', rid))
    return '; '.join(out)

new = {}   # id -> content / fields computed here

# ---- prisma
P = json.load(open(R + 'prisma.json'))
nrep = P['included']['studies']
companions = [r for r in ('R0006', 'R0484') if r in INC]
if len(companions) == 2:
    studies_n = nrep - 1
    note = f'{nrep} included reports correspond to {studies_n} studies (R0006 and R0484 are two reports of one study)'
else:
    studies_n = nrep
    note = f'{nrep} included reports correspond to {studies_n} studies (no two included reports share a study)'
assert nrep == len(INC) or args.old_set, (nrep, len(INC))
new['prisma-counts'] = {'content': {**P, 'studies_note': note}}

# ---- per-year, venues, keywords
yrs = collections.Counter(rec[r]['year'] for r in ids if rec[r].get('year'))
new['per-year'] = {'content': {str(y): n for y, n in sorted(yrs.items())}}
ven = collections.Counter()
for r in ids:
    v = rec[r].get('venue')
    if v: ven['Sustainability' if v == 'Sustainability (Switzerland)' else v] += 1
new['venues'] = {'content': {'top_venues_merged': [[v, n] for v, n in ven.most_common(10)],
                             'note': 'Sustainability and Sustainability (Switzerland) are one journal and are merged'}}
ksets = [sorted({k.strip().lower() for k in rec[r].get('keywords') or [] if k and k.strip()}) for r in ids]
kc = collections.Counter(k for ks in ksets for k in ks)
pc = collections.Counter(p for ks in ksets for p in itertools.combinations(ks, 2))
new['keywords'] = {'content': {'top_keywords': [{'keyword': k, 'count': n} for k, n in kc.most_common(12)],
                               'top_cooccurrence': [{'a': a, 'b': b, 'count': n} for (a, b), n in pc.most_common(10)]}}

# ---- scientometrics
s1 = json.load(open(S + 'rq1-scientometrics.json'))
new['collaboration'] = {'content': {'matched_in_openalex': s1['matched'], 'included': len(ids),
                                    'countries_top': dict(list(s1['countries'].items())[:10]),
                                    'international_collaboration_share': s1['international_collaboration_share'],
                                    'citations_total': s1['citations_total']}}

# ---- tables read from the CSVs written by build_tables.py
def rows_of(name, fix_group=False):
    rows = list(csv.reader(open(S + 'tables/%s.csv' % name)))[1:]
    out = []
    for r in rows:
        if fix_group and r[0] in LONG: r = [LONG[r[0]]] + r[1:]
        out.append(' & '.join(r))
    return out
for tid, fix in [('t-characteristics-sector', True), ('t-characteristics-method', True), ('t-appraisal', False),
                 ('t-appraisal-group', False), ('t-institutions', False), ('t-geography', False)]:
    new[tid] = {'rows': rows_of(tid, fix)}
new['t-appraisal']['caption'] = 'Quality appraisal of the %d included reports (yes = 1, partly = 0.5, no = 0).' % len(ids)
new['t-institutions']['caption'] = 'Most productive institutions (OpenAlex affiliations, %d of %d studies matched).' % (s1['matched'], len(ids))
new['characteristics-notes'] = {'content': {
    'one_group_one_sector': 'each study has one technology value and one sector value, so it appears in exactly one technology group and one sector; table totals are %d reports' % len(ids),
    'supplementary': 'Supplementary Table S1 (s-included-studies.csv) lists all %d included reports with year, authors, title, venue, DOI, technology, technology group, theme, study type, sector, scope, departments, method, outcomes, extraction tier and the five appraisal answers and score' % len(ids)}}

# ---- RQ3
cb3 = json.load(open(S + 'rq3-codebook.json'))['codes']
r3 = [r for r in jl(S + 'rq3-coded.jsonl') if r['record_id'] in INC]
CLASS = {'policy-regulatory': 'Policy and regulation', 'economic-financial': 'Economics and finance', 'market': 'Markets and supply chains',
         'technical-infrastructure': 'Technical infrastructure', 'institutional-governance': 'Institutions and governance',
         'social-cultural': 'Social acceptance and justice', 'knowledge-capacity': 'Knowledge and capacity', 'environmental-resource': 'Natural resources and climate'}
for c in cb3:
    parts = []
    for side in ('barriers', 'enablers'):
        ents = [(r['record_id'], x) for r in sorted(r3, key=lambda r: r['record_id']) for x in r[side] if c['id'] in x['codes'] and 'flag' not in x]
        studies = {rid for rid, _ in ents}
        if not studies: parts.append(f'{side.upper()}: 0 studies.'); continue
        parts.append(f'{side.upper()}: {len(studies)} studies; by technology group: {by_group(studies)}. Example items (verbatim, with study): {first_items(ents)}')
    if all(p.endswith('0 studies.') for p in parts): dropped.append('rq3-' + c['id']); new['rq3-' + c['id']] = None; continue
    new['rq3-' + c['id']] = {'content': "Open-problem class '%s', code '%s' (definition: %s). %s" % (CLASS[c['domain']], c['label'], c['definition'], ' '.join(parts))}
new['rq3-frame'] = {'content': 'RQ3 theme: barriers and enablers of technology adoption. %d included studies reported RQ3 data (tier-2 extraction); each barrier or enabler item was coded manually into %d codes grouped into the eight open-problem classes named in the background (%s). A study counts once per code and side. Technology groups use the six groups of RQ2.' % (len(r3), len(cb3), '; '.join(CLASS.values()))}
new['t-rq3-barriers-enablers'] = {'content': 'Table Tables/t-rq3-barriers-enablers, label tab:rq3: Barriers and enablers reported by the %d tier-2 studies with RQ3 data; a study counts once per code and side.' % len(r3)}

# ---- RQ4
cb4 = json.load(open(S + 'rq4-codebook.json'))
r4 = [r for r in jl(S + 'rq4-coded.jsonl') if r['record_id'] in INC]
# rq4 items are counted as in build_summaries.py (flagged items are not filtered for RQ4)
for c in cb4['impacts']:
    if c['id'] == 'other': continue
    ents = [(r['record_id'], x) for r in sorted(r4, key=lambda r: r['record_id']) for x in r['impacts'] if c['id'] in x['codes']]
    studies = {rid for rid, _ in ents}
    if not studies: dropped.append('rq4-' + c['id']); new['rq4-' + c['id']] = None; continue
    d = {k: len({rid for rid, x in ents if x['direction'] == k}) for k in ('positive', 'negative', 'mixed')}
    new['rq4-' + c['id']] = {'content': "Impact '%s' (domain %s): %d studies; positive %d, negative %d, mixed %d; by technology group: %s. Example items (verbatim, direction, study): %s" % (
        c['label'], c['domain'], len(studies), d['positive'], d['negative'], d['mixed'], by_group(studies), first_items(ents, True))}
for c in cb4['gaps']:
    if c['id'] == 'other': continue
    ents = [(r['record_id'], x) for r in sorted(r4, key=lambda r: r['record_id']) for x in r['gaps'] if c['id'] in x['codes']]
    studies = {rid for rid, _ in ents}
    if not studies: dropped.append('rq4-gap-' + c['id']); new['rq4-gap-' + c['id']] = None; continue
    new['rq4-gap-' + c['id']] = {'content': "Research gap '%s': %d studies; by technology group: %s. Example items (verbatim, study): %s" % (
        c['label'], len(studies), by_group(studies), first_items(ents, n=4))}
new['rq4-frame'] = {'content': 'RQ4 theme: social, environmental and territorial impacts and conflicts, and the research gaps the studies state. %d included studies were coded; impacts carry a direction (positive, negative, mixed) and a study can report one impact in more than one direction.' % len(r4)}

# ---- RQ2 from rq2/gN-table.json (any number of rows)
RQ2NAME = {1: 'Renewable generation (solar, wind, hydropower, geothermal and ocean energy)', 2: 'Bioenergy',
           3: 'Smart grids, microgrids and energy storage', 4: 'Demand-side technologies (energy efficiency and electromobility)',
           5: 'Low-carbon fuels (hydrogen, carbon capture and nuclear)', 6: 'System-level planning, policy and other'}
CAPNAME = {1: 'Renewable generation: solar, wind, hydropower, geothermal and ocean energy', 2: 'Bioenergy',
           3: 'Smart grids, microgrids and energy storage', 4: 'Demand side: energy efficiency and electromobility',
           5: 'Low-carbon fuels: hydrogen, carbon capture and nuclear', 6: 'System-level planning'}
txt = lambda v: v if isinstance(v, str) else '; '.join(v)
rq2_records = {}   # id -> dict, in order
bad = []
for g in range(1, 7):
    t = json.load(open(S + 'rq2/g%d-table.json' % g)); rows = t['rows']
    for row in rows:
        for s in row['studies']:
            if s not in INC: bad.append((g, s))
    allst = [s for row in rows for s in row['studies']]
    subs = '; '.join('%s (%s)' % (row['sub_theme'], row['n']) for row in rows)
    rq2_records['rq2-g%d' % g] = {'source': 'review/synthesis/rq2/g%d-table.json' % g, 'content': (
        'Theme (technology group %d) for RQ2: %s. It holds %d included reports, split into %d sub-themes: %s. '
        'Dimensions compared: study type and method, setting (sector and department), technical, economic and environmental outcomes. '
        'Cite the whole group as \\cite{%s}.' % (g, RQ2NAME[g], t['n_studies'], len(rows), subs, ','.join(allst)))}
    cap = 'RQ2 comparison: %s (%d studies). Reported values per sub-theme are in Supplementary Table S%d.' % (CAPNAME[g], t['n_studies'], g + 1)
    rq2_records['t-rq2-g%d' % g] = {'source': 'paper/Tables/t-rq2-g%d.tex' % g, 'label': 'tab:rq2-g%d' % g, 'caption': cap,
        'content': 'Comparison table for group %d, file Tables/t-rq2-g%d, label tab:rq2-g%d; caption: %s' % (g, g, g, cap)}
    for k, row in enumerate(rows, 1):
        rq2_records['rq2-g%d-s%d' % (g, k)] = {'source': 'review/synthesis/rq2/g%d-table.json row %d' % (g, k), 'content': (
            "Sub-theme '%s' of group %d: %d studies, cite as \\cite{%s}. Methods: %s. Settings: %s. Technical outcomes: %s. "
            "Economic outcomes: %s. Environmental outcomes: %s. Pattern: %s (Values are the extracted values; each bracketed record id is the "
            "study reporting that value and is cited as \\cite{<id>}.)" % (row['sub_theme'], g, row['n'], ','.join(row['studies']), txt(row['methods']),
            txt(row['settings']), txt(row['technical']), txt(row['economic']), txt(row['environmental']), txt(row['pattern'])))}
if bad: print('WARNING: rq2 tables cite studies outside the included set:', bad[:20], '(%d total)' % len(bad), file=sys.stderr)

# ---- assemble in template order
tmpl = json.load(open(args.template))
out = []; seen = set(); rq2_done = False
for r in tmpl:
    i = r['id']
    if re.match(r'(t-)?rq2-g\d(-s\d+)?$', i):
        if not rq2_done:
            for k, v in rq2_records.items():
                out.append({'id': k, 'regime': r['regime'], **v})
            rq2_done = True
        continue
    if i in new:
        if new[i] is None: continue
        n = new[i]
        if 'rows' in n:   # table record: content is a dict with caption, label, header, rows
            c = dict(r['content']); c['rows'] = n['rows']
            if 'caption' in n: c['caption'] = n['caption']
            r = {**r, 'content': c}
        else:
            r = {**r, **n}
    out.append(r)
# records not touched here (excluded-examples, prisma-figure) are kept as in the template
json.dump(out, open(args.out, 'w'), indent=1, ensure_ascii=False)
print('records', len(out), 'rq2 records', len(rq2_records), 'dropped (count 0):', dropped or 'none', file=sys.stderr)
