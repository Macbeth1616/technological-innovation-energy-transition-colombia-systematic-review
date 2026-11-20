"""Write paper/included.bib with one entry per included study (key = record id).
Same entry format as build_rq2_tables.py, without rendering the RQ2 tables. Run from the repo root."""
import json, ast, sys
sys.path.insert(0, 'review/synthesis')
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
