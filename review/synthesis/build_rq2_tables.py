"""Render the RQ2 comparison tables (review/synthesis/rq2/gN-table.json) as LaTeX and CSV,
and write paper/included.bib with one entry per included study (key = record id)."""
import json, csv, re, ast
NAMES = {1: 'Renewable generation: solar, wind, hydropower, geothermal and ocean energy',
         2: 'Bioenergy', 3: 'Smart grids, microgrids and energy storage',
         4: 'Demand side: energy efficiency and electromobility',
         5: 'Low-carbon fuels: hydrogen, carbon capture and nuclear', 6: 'System-level planning'}
def esc(s):
    s = str(s).replace('\\', r'\textbackslash{}')
    s = re.sub(r'([&%$#_{}])', r'\\\1', s)
    return s.replace('~', r'\textasciitilde{}').replace('^', r'\^{}')
def cites(s):  # "[R0012, R0345]" -> \cite{R0012,R0345}
    return re.sub(r'\\\{?\[?((?:R\d{4}(?:,\s*)?)+)\]', lambda m: '\\cite{' + ','.join(re.findall(r'R\d{4}', m.group(1))) + '}', s)
def bare(v):  # remaining bare ids outside \\cite{...} become citations
    parts = re.split(r'(\\cite\{[^}]*\})', v)
    return ''.join(x if x.startswith('\\cite') else re.sub(r"(R\d{4})(?:'s)?", r'\\cite{\1}', x) for x in parts)
def cell(v):
    v = v if isinstance(v, str) else ' | '.join(v)
    v = esc(v).replace('/', '/\\allowbreak{}')
    v = re.sub(r'\(((?:R\d{4}(?:,\s*(?:and\s*)?)?)+)\)', lambda m: '[' + ', '.join(re.findall(r'R\d{4}', m.group(1))) + ']', v)
    return bare(re.sub(r'\[((?:R\d{4}(?:,\s*)?)+)\]', lambda m: '\\cite{' + ','.join(re.findall(r'R\d{4}', m.group(1))) + '}', v))
for g in range(1, 7):
    t = json.load(open(f'review/synthesis/rq2/g{g}-table.json'))
    with open(f'review/synthesis/tables/t-rq2-g{g}.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['sub_theme', 'n', 'studies', 'methods', 'settings', 'technical', 'economic', 'environmental', 'pattern'])
        for r in t['rows']:
            w.writerow([r['sub_theme'], r['n'], ' '.join(r['studies'])] + [r[k] if isinstance(r[k], str) else ' | '.join(r[k]) for k in ('methods', 'settings', 'technical', 'economic', 'environmental', 'pattern')])
    with open(f'paper/Tables/t-rq2-g{g}.tex', 'w') as f:
        f.write('{\\footnotesize\\setlength{\\tabcolsep}{4pt}\n\\begin{longtable}{>{\\raggedright\\arraybackslash}p{3.6cm}r>{\\raggedright\\arraybackslash}p{4.1cm}>{\\raggedright\\arraybackslash}p{6.4cm}}\n')
        f.write('\\caption{Comparison of the theme %s (%d studies). Reported values per sub-theme are in Supplementary Table S%d.}\\label{tab:rq2-g%d}\\\\\n' % (NAMES[g], t['n_studies'], g + 1, g))
        H = 'Sub-theme & $n$ & Dominant methods & What the evidence supports \\\\\n'
        f.write('\\toprule\n' + H + '\\midrule\n\\endfirsthead\n\\toprule\n' + H + '\\midrule\n\\endhead\n')
        for r in t['rows']:
            m = r['methods'] if isinstance(r['methods'], str) else '; '.join(r['methods'])
            m = re.sub(r'\s*\([^()]*\)', '', m)
            f.write(' & '.join([esc(r['sub_theme']) + ' \\cite{' + ','.join(r['studies']) + '}', str(r['n']), cell(m), cell(r['pattern'])]) + ' \\\\\n')
        f.write('\\bottomrule\n\\end{longtable}}\n')
# bibliography of included studies
from included_ids import included
ex = set(included())
rec = {json.loads(l)['id']: json.loads(l) for l in open('review/records.jsonl')}
# metadata verified by the operator at the publisher (amendment 3)
OVERRIDES = {'R0762': {'type': 'proceedings-article', 'venue': '2022 IEEE PES Generation, Transmission and Distribution Conference and Exposition -- Latin America (IEEE PES GTD Latin America)'}}
with open('paper/included.bib', 'w') as f:
    B = lambda x: str(x).replace('\ufffd', '').replace('&', r'\&')
    for rid in sorted(ex):
        r = {k: (B(v) if k in ('title', 'venue') else v) for k, v in rec[rid].items()}
        try: au = ast.literal_eval(r['authors']) if isinstance(r['authors'], str) else r['authors']
        except Exception: au = [r['authors']]
        r.update(OVERRIDES.get(rid, {}))
        typ = 'inproceedings' if r.get('type') in ('CONF', 'CPAPER', 'proceedings-article') else 'article'
        venue = 'booktitle' if typ == 'inproceedings' else 'journal'
        f.write('@%s{%s,\n  author = {%s},\n  title = {{%s}},\n  %s = {%s},\n  year = {%s},\n  doi = {%s}\n}\n\n' % (
            typ, rid, ' and '.join(au), r['title'], venue, r['venue'], r['year'], r['doi']))
print('ok')
