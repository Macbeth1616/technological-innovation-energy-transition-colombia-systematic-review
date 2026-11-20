"""Rebuild rq1-scientometrics.json and rq3-rq4-summary.json for the included studies."""
import json, collections, itertools, sys
sys.path.insert(0, 'review/synthesis')
from included_ids import included
INC = set(included())
W = {k: v for k, v in json.load(open('review/synthesis/openalex-works.json')).items() if k in INC}
B = json.load(open('review/biblio.json'))
inst = collections.Counter(); names = {}; ctry = collections.Counter(); pairs = collections.Counter(); intl = 0; n = 0; cit = []
topics = collections.Counter(); field = collections.Counter()
for rid, w in W.items():
    if not w: continue
    n += 1; cit.append((w['cited_by_count'], rid))
    I = set(); C = set()
    for a in w['authorships']:
        for i in a.get('institutions', []): I.add(i['id']); names[i['id']] = i['display_name']
        C |= set(a.get('countries', []))
    inst.update(I); ctry.update(C); intl += bool(C - {'CO'})
    pairs.update(itertools.combinations(sorted(I), 2))
    pt = w.get('primary_topic') or {}
    if pt: topics[pt['display_name']] += 1; field[pt.get('subfield', {}).get('display_name')] += 1
out = {'basis': 'included studies matched in OpenAlex by DOI', 'included': len(INC), 'matched': n, 'unmatched': sorted(k for k, v in W.items() if not v),
       'international_collaboration_share': round(intl / n, 3), 'citations_total': sum(c for c, _ in cit),
       'top_cited': [{'record_id': r, 'cited_by': c} for c, r in sorted(cit, reverse=True)[:15]],
       'top_institutions': [{'name': names[i], 'studies': c} for i, c in inst.most_common(25)],
       'countries': dict(ctry.most_common()),
       'top_institution_pairs': [{'a': names[a], 'b': names[b], 'studies': c} for (a, b), c in pairs.most_common(20)],
       'top_subfields': dict(field.most_common(12)), 'top_topics': dict(topics.most_common(15)),
       'per_year': B['per_year'], 'top_venues': B['top_venues'][:15]}
json.dump(out, open('review/synthesis/rq1-scientometrics.json', 'w'), indent=1, ensure_ascii=False)

ex = {}
for l in open('review/extraction.jsonl'): r = json.loads(l); ex[r['record_id']] = r
tech = lambda rid: ex[rid]['data']['technology']['value']
cb3 = json.load(open('review/synthesis/rq3-codebook.json'))['codes']; cb4 = json.load(open('review/synthesis/rq4-codebook.json'))
s = {'rq3': {}, 'rq4_impacts': {}, 'rq4_gaps': {}}
r3 = [r for r in map(json.loads, open('review/synthesis/rq3-coded.jsonl')) if r['record_id'] in INC]
for c in cb3:
    d = {}
    for side in ('barriers', 'enablers'):
        S = {r['record_id'] for r in r3 for x in r[side] if c['id'] in x['codes'] and 'flag' not in x}
        d[side] = {'studies': len(S), 'top_technologies': collections.Counter(tech(x) for x in S).most_common(4)}
    s['rq3'][c['id']] = {'label': c['label'], 'domain': c['domain'], **d}
r4 = [r for r in map(json.loads, open('review/synthesis/rq4-coded.jsonl')) if r['record_id'] in INC]
for c in cb4['impacts']:
    S = collections.defaultdict(set)
    for r in r4:
        for x in r['impacts']:
            if c['id'] in x['codes']: S[x['direction']].add(r['record_id']); S['all'].add(r['record_id'])
    s['rq4_impacts'][c['id']] = {'label': c['label'], 'domain': c['domain'], 'studies': len(S['all']), **{k: len(S[k]) for k in ('positive', 'negative', 'mixed')},
                                 'top_technologies': collections.Counter(tech(x) for x in S['all']).most_common(4)}
for c in cb4['gaps']:
    S = {r['record_id'] for r in r4 for x in r['gaps'] if c['id'] in x['codes']}
    s['rq4_gaps'][c['id']] = {'label': c['label'], 'studies': len(S), 'top_technologies': collections.Counter(tech(x) for x in S).most_common(3)}
json.dump(s, open('review/synthesis/rq3-rq4-summary.json', 'w'), indent=1, ensure_ascii=False)
print('included', len(INC), 'matched', n, 'intl', out['international_collaboration_share'], 'cit', out['citations_total'])
