"""Build the review's data-driven tables (CSV + LaTeX) from review/ records."""
import json, csv, collections, re
R = 'review/'; T = 'paper/Tables/'; C = 'review/synthesis/tables/'
ex = {}; ap = {}
for l in open(R + 'extraction.jsonl'): r = json.loads(l); ex[r['record_id']] = r
for l in open(R + 'appraisal.jsonl'): r = json.loads(l); ap[r['record_id']] = r
rec = {json.loads(l)['id']: json.loads(l) for l in open(R + 'records.jsonl')}
reg = {json.loads(l)['record_id']: json.loads(l) for l in open(R + 'synthesis/regions-norm.jsonl')}
G = {'Renewable generation (solar, wind, hydro, geothermal, ocean)': ['solar', 'wind', 'hydropower', 'geothermal', 'ocean-energy'],
     'Bioenergy': ['biomass-bioenergy'],
     'Grids, microgrids and storage': ['smart-grids-digitalization', 'microgrids-off-grid', 'energy-storage'],
     'Demand side (efficiency, electromobility)': ['energy-efficiency', 'electromobility'],
     'Low-carbon fuels (hydrogen, CCS, nuclear)': ['hydrogen-low-carbon-fuels', 'carbon-capture-storage', 'nuclear'],
     'System-level planning and other': ['multiple-or-system-level', 'other']}
grp = {t: g for g, ts in G.items() for t in ts}
SHORT = dict(zip(G, ['Renewables', 'Bioenergy', 'Grids/storage', 'Demand side', 'Low-carbon fuels', 'System-level']))
V = lambda rid, k: ex[rid]['data'][k]['value']
from included_ids import included
ids = included()

def tex_escape(s):
    return re.sub(r'([&%$#_{}])', r'\\\1', str(s)).replace('~', r'\textasciitilde{}')

def write(name, header, rows, caption, label, colspec=None):
    with open(C + name + '.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)
    colspec = colspec or 'l' + 'r' * (len(header) - 1)
    with open(T + name + '.tex', 'w') as f:
        f.write('\\begin{table}[htbp]\n\\centering\n\\footnotesize\\setlength{\\tabcolsep}{4pt}\n\\caption{%s}\n\\label{%s}\n' % (caption, label))
        f.write('\\begin{adjustbox}{max width=0.98\\textwidth}\n\\begin{tabular}{%s}\n\\toprule\n' % colspec)
        f.write(' & '.join(tex_escape(h) for h in header) + ' \\\\\n\\midrule\n')
        for r in rows: f.write(' & '.join(tex_escape(x) for x in r) + ' \\\\\n')
        f.write('\\bottomrule\n\\end{tabular}\n\\end{adjustbox}\n\\end{table}\n')

# T1 characteristics: technology group x sector
secs = ['power-generation-SIN', 'non-interconnected-zones', 'buildings-residential', 'buildings-commercial-institutional',
        'industry', 'transport', 'agriculture', 'multi-sector']
sh = ['SIN', 'ZNI', 'Resid.', 'Comm./inst.', 'Industry', 'Transport', 'Agric.', 'Multi']
rows = []
for g in G:
    s = [r for r in ids if grp[V(r, 'technology')] == g]
    c = collections.Counter(V(r, 'sector') for r in s)
    rows.append([SHORT[g], len(s)] + [c[x] for x in secs])
c = collections.Counter(V(r, 'sector') for r in ids)
rows.append(['Total', len(ids)] + [c[x] for x in secs])
write('t-characteristics-sector', ['Technology group', 'Studies'] + sh, rows,
      'Included reports by technology group and energy sector (each study in one group and one sector). SIN: National Interconnected System; ZNI: non-interconnected zones; Renewables: solar, wind, hydropower, geothermal and ocean energy; Grids/storage: smart grids, microgrids and storage; Demand side: efficiency and electromobility; Low-carbon fuels: hydrogen, carbon capture and nuclear.', 'tab:characteristics-sector')

# T2 technology group x study type and period
types = ['modelling-simulation', 'techno-economic-assessment', 'empirical-case-study', 'review', 'policy-analysis', 'qualitative-social-study', 'other']
th = ['Model.', 'Tech-econ.', 'Empir.', 'Review', 'Policy', 'Qual.', 'Other', '2015-18', '2019-21', '2022-25']
per = lambda y: '2015-18' if y <= 2018 else ('2019-21' if y <= 2021 else '2022-25')
rows = []
for g in G:
    s = [r for r in ids if grp[V(r, 'technology')] == g]
    c = collections.Counter(V(r, 'study_type') for r in s); p = collections.Counter(per(int(rec[r]['year'])) for r in s)
    rows.append([SHORT[g]] + [c[x] for x in types] + [p[x] for x in ('2015-18', '2019-21', '2022-25')])
write('t-characteristics-method', ['Technology group'] + th, rows,
      'Included reports by technology group, study type and publication period (group abbreviations as in Table~\\ref{tab:characteristics-sector}). Model.: modelling and simulation; Tech-econ.: techno-economic assessment; Empir.: empirical case study; Qual.: qualitative social study.', 'tab:characteristics-method')

# T3 appraisal
rows = []
for q, lab in [('QA1', 'Aims stated'), ('QA2', 'Colombian context defined'), ('QA3', 'Method reproducible or assessable'),
               ('QA4', 'Results clearly reported and supported'), ('QA5', 'Limitations discussed')]:
    c = collections.Counter(ap[r]['answers'][q] for r in ids)
    rows.append([q + ' ' + lab, c['yes'], c['partly'], c['no']])
write('t-appraisal', ['Appraisal question', 'Yes', 'Partly', 'No'], rows,
      'Quality appraisal of the %d included reports' % len(ids) + ' (yes = 1, partly = 0.5, no = 0).', 'tab:appraisal')
rows = []
for g in G:
    s = [ap[r]['score'] for r in ids if grp[V(r, 'technology')] == g]
    s = sorted(float(x) for x in s); rows.append([g, len(s), f'{sum(s)/len(s):.2f}', f'{s[len(s)//2]:.1f}', sum(1 for x in s if x >= 4)])
write('t-appraisal-group', ['Technology group', 'Studies', 'Mean score', 'Median', 'Score >= 4'], rows,
      'Appraisal score (0-5) by technology group.', 'tab:appraisal-group')

# T4 geography
c = collections.Counter(reg[r]['scope'] for r in ids)
mac = collections.Counter(m for r in ids for m in reg[r]['macro_regions'])
dep = collections.Counter(d for r in ids for d in reg[r]['departments'])
rows = [['Scope: ' + k, c[k]] for k in ('national', 'regional', 'local', 'unspecified')]
rows += [['Macro-region: ' + k, v] for k, v in mac.most_common()]
rows += [['Department: ' + k, v] for k, v in dep.most_common(12)]
write('t-geography', ['Geographic coverage', 'Studies'], rows,
      'Geographic coverage of the included studies; a regional or local study can cover several departments and macro-regions.', 'tab:geography')

# T5 RQ1 institutions / countries
s1 = json.load(open(R + 'synthesis/rq1-scientometrics.json'))
rows = [[x['name'], x['studies']] for x in s1['top_institutions'][:15]]
write('t-institutions', ['Institution', 'Studies'], rows,
      'Most productive institutions (OpenAlex affiliations, %d of %d studies matched).' % (s1['matched'], len(ids)), 'tab:institutions')

# T6 RQ3 barriers/enablers
s = json.load(open(R + 'synthesis/rq3-rq4-summary.json'))
TECH = {'multiple-or-system-level': 'system-level', 'biomass-bioenergy': 'bioenergy', 'microgrids-off-grid': 'microgrids', 'smart-grids-digitalization': 'smart grids', 'hydrogen-low-carbon-fuels': 'hydrogen', 'energy-efficiency': 'efficiency', 'electromobility-transport': 'electromobility', 'energy-storage': 'storage'}
TL = lambda lst: '; '.join(f"{TECH.get(t, t.replace('-', ' '))} ({n})" for t, n in lst[:3])
CLASS = {'policy-regulatory': 'Policy and regulation', 'economic-financial': 'Economics and finance', 'market': 'Markets and supply chains',
         'technical-infrastructure': 'Technical infrastructure', 'institutional-governance': 'Institutions and governance',
         'social-cultural': 'Social acceptance and justice', 'knowledge-capacity': 'Knowledge and capacity', 'environmental-resource': 'Natural resources and climate'}
CORDER = list(CLASS)
rows = []
for cid, v in sorted(s['rq3'].items(), key=lambda kv: (CORDER.index(kv[1]['domain']), -kv[1]['barriers']['studies'])):
    rows.append([CLASS[v['domain']], v['label'], v['barriers']['studies'], v['enablers']['studies'], TL(v['barriers']['top_technologies'])])
write('t-rq3-barriers-enablers', ['Open-problem class', 'Code', 'Barrier', 'Enabler', 'Top technologies (barrier side)'], rows,
      'Barriers and enablers reported by the %d included in-depth studies with barrier or enabler data; the barrier and enabler columns count studies, and a study counts once per code and side.' % len({json.loads(l)['record_id'] for l in open(R + 'synthesis/rq3-coded.jsonl')} & set(ids)),
      'tab:rq3', 'p{2.6cm}p{4cm}rrp{4.2cm}')
# T7 RQ4 impacts
rows = [[v['domain'], v['label'], v['studies'], v['positive'], v['negative'], v['mixed'], TL(v['top_technologies'])]
        for cid, v in sorted(s['rq4_impacts'].items(), key=lambda kv: (kv[1]['domain'], -kv[1]['studies'])) if cid != 'other']
write('t-rq4-impacts', ['Domain', 'Impact', 'Studies', 'Positive', 'Negative', 'Mixed', 'Most frequent technologies'], rows,
      'Social, environmental and territorial impacts by direction; a study can report the same impact in more than one direction.', 'tab:rq4', 'p{2.4cm}p{3.8cm}rrrrp{4cm}')
# T8 gaps
rows = [[v['label'], v['studies'], TL(v['top_technologies'])] for cid, v in sorted(s['rq4_gaps'].items(), key=lambda kv: -kv[1]['studies']) if cid != 'other']
write('t-research-gaps', ['Research gap', 'Studies', 'Most frequent technologies'], rows,
      'Research gaps stated by the included studies.', 'tab:gaps', 'lrp{6cm}')

# Supplementary: all included studies
with open(C + 's-included-studies.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['record_id', 'study_group', 'year', 'authors', 'title', 'venue', 'doi', 'technology', 'technology_group', 'theme', 'study_type',
                'sector', 'scope', 'departments', 'method', 'outcomes', 'extraction_tier', 'QA1', 'QA2', 'QA3', 'QA4', 'QA5', 'qa_score'])
    for r in ids:
        d = ex[r]['data']; a = ap[r]['answers']
        w.writerow([r, d['study_group']['value'], rec[r]['year'], rec[r]['authors'], rec[r]['title'], rec[r]['venue'], rec[r]['doi'],
                    V(r, 'technology'), grp[V(r, 'technology')], V(r, 'theme'), V(r, 'study_type'), V(r, 'sector'), reg[r]['scope'],
                    '; '.join(reg[r]['departments']), d['method']['value'], d['outcomes']['value'], d['extraction_tier']['value'],
                    a['QA1'], a['QA2'], a['QA3'], a['QA4'], a['QA5'], ap[r]['score']])
print('ok')
