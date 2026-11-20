"""Build review/synthesis/evidence/discussion.json: evidence-maturity axis records for the Discussion."""
import json, collections, statistics, sys
sys.path.insert(0, 'review/synthesis')
from included_ids import included
exec(open('review/synthesis/build_tables.py').read().split('SHORT =')[0].split('V = ')[0])  # G, grp, ex, ap
ids = included()
STAGE = {'modelling-simulation': 'model-based', 'techno-economic-assessment': 'model-based',
         'empirical-case-study': 'field and case', 'policy-analysis': 'institutional and social',
         'qualitative-social-study': 'institutional and social', 'review': 'secondary synthesis', 'other': 'secondary synthesis'}
SH = dict(zip(G, ['renewable generation', 'bioenergy', 'grids, microgrids and storage', 'demand side',
                  'low-carbon fuels', 'system-level planning']))
st = lambda r: STAGE[ex[r]['data']['study_type']['value']]
g = lambda r: SH[grp[ex[r]['data']['technology']['value']]]
out = []
by = collections.defaultdict(list)
for r in ids: by[st(r)].append(r)
for s in ['model-based', 'field and case', 'institutional and social', 'secondary synthesis']:
    rs = by[s]; sc = [ap[r]['score'] for r in rs]
    qa5 = collections.Counter(ap[r]['answers']['QA5'] for r in rs)
    qa3 = collections.Counter(ap[r]['answers']['QA3'] for r in rs)
    types = collections.Counter(ex[r]['data']['study_type']['value'] for r in rs)
    pg = collections.Counter(g(r) for r in rs)
    tot = {gg: sum(1 for r in ids if g(r) == gg) for gg in SH.values()}
    share = {gg: f'{pg[gg]} of {tot[gg]} ({100*pg[gg]/tot[gg]:.0f}%)' for gg in SH.values()}
    out.append({'id': 'stage-' + s.split()[0], 'regime': 'none', 'source': 'review/extraction.jsonl study_type + review/appraisal.jsonl',
                'content': (f"Evidence-maturity stage '{s}' (study types: " + '; '.join(f'{k} {v}' for k, v in types.most_common()) +
                            f"): {len(rs)} of {len(ids)} included reports. By technology group (stage count of group total): " +
                            '; '.join(f'{k} {v}' for k, v in share.items()) +
                            f". Appraisal: mean score {statistics.mean(sc):.2f}, median {statistics.median(sc)}; QA3 method reproducible yes {qa3['yes']}, partly {qa3['partly']}, no {qa3['no']}; QA5 limitations discussed yes {qa5['yes']}, partly {qa5['partly']}, no {qa5['no']}. "
                            "Cite the stage as a group: \\cite{" + ','.join(rs) + "}. Per group cite lists: " +
                            ' | '.join(f"{gg}: \\cite{{{','.join(r for r in rs if g(r)==gg)}}}" for gg in SH.values() if pg[gg]))})
json.dump(out, open('review/synthesis/evidence/discussion.json', 'w'), ensure_ascii=False, indent=1)
for o in out: print(o['content'][:700], '\n')
# copies of records the Discussion interprets (same ids, same content)
I = {x['id']: x for x in json.load(open('review/synthesis/evidence/introduction.json'))}
R = {x['id']: x for x in json.load(open('review/synthesis/evidence/results.json'))}
for k in ['protocol-rqs', 'gap-analysis', 'scope-reviews']: out.append(I[k])
for k in ['per-year', 'collaboration', 't-geography', 't-institutions', 't-appraisal', 'rq3-frame', 't-rq3-barriers-enablers', 'rq4-frame', 't-rq4-impacts', 't-research-gaps'] + \
         [k for k in R if k.startswith('rq3-') or k.startswith('rq4-')]:
    if R[k] not in out: out.append(R[k])
out.append({'id': 'source-inconsistencies', 'regime': 'none', 'source': 'review/synthesis/values-to-verify.md', 'content': 'Of the eight cases of values that look inconsistent in the source itself (operator decision 2026-11-18), four involve included studies and are kept as reported and cited to the study: the same scenarios (11.4 and 22.6 MtCO2-eq) with 5-11% and 5-10% shares in two papers that are likely not independent \\cite{R0152,R0520}; the same Pareto solutions (A1, A10) reported with opposite signs for profit and NPV in a second paper, which is not in the included set \\cite{R0045}; a La Guajira wind power density of 482 W/m2 against 796 W/m2 in a second paper, possibly different heights or periods, which is not in the included set \\cite{R0367}; 12 against nine biodiesel plants in a second paper, a different scope or year, which is not in the included set \\cite{R0272}. For the last three cases the counterpart report was excluded under E8 (reference budget), so the inconsistency is noted but cannot be shown within the included set (operator decision 2026-11-19). The other four cases cite only studies outside the included set and are not reported. Four cases across five included reports.'})
json.dump(out, open('review/synthesis/evidence/discussion.json', 'w'), ensure_ascii=False, indent=1)
print(len(out), 'records')
