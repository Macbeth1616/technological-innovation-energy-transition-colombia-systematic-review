"""Build review/synthesis/evidence/limitations.json from methods/results/discussion records."""
import json
M = {x['id']: x for x in json.load(open('review/synthesis/evidence/methods.json'))}
R = {x['id']: x for x in json.load(open('review/synthesis/evidence/results.json'))}
D = {x['id']: x for x in json.load(open('review/synthesis/evidence/discussion.json'))}
out = [M[k] for k in ['prisma-counts', 'searches', 'search-limits', 'eligibility-criteria', 'screening-process', 'kappa',
                       'full-text-retrieval', 'data-extraction', 'appraisal', 'synthesis-coding', 'synthesis-scientometrics',
                       'no-meta-analysis', 'certainty', 'protocol-amendments']]
out += [R['t-appraisal'], R['t-characteristics-method']]
out += [D[k] for k in ['stage-model-based', 'stage-field', 'stage-institutional', 'stage-secondary', 'source-inconsistencies']]
out.append({'id': 'protocol-registration', 'regime': 'none', 'source': 'paper/main.tex methods.m-protocol-registration',
            'content': 'The review protocol was not prospectively registered; it was approved internally by the review operator on 2026-11-17 and amended four times (three times on 2026-11-18 and once on 2026-11-19), each amendment documented.'})
out.append({'id': 'sources-not-searched', 'regime': 'none', 'source': 'review/searches.jsonl',
            'content': 'Only two sources were searched, Scopus (545 records) and OpenAlex (1333 records); Web of Science, IEEE Xplore, ScienceDirect, SciELO, Redalyc and grey literature (theses, technical reports, government and utility documents) were not searched, and grey literature was excluded by criterion E3.'})
out.append({'id': 'external-literature', 'regime': 'none', 'source': 'guidance/introduction, guidance/background',
            'content': 'The external literature used in the introduction, background and discussion (45 papers) was limited to papers whose full text could be downloaded in open access; five existing reviews could not be obtained in full text and were not compared, and three context topics (the Colombian NDC, El Nino effects on the power system, Latin American just transition) had no open-access source.'})
out.append({'id': 'reference-budget-bias', 'regime': 'none', 'source': 'review/prioritization.json; review/extraction.jsonl; review/protocol.json (E8)',
            'content': 'Criterion E8 excluded 364 eligible studies (of 521) to meet the reference budget of 157 included studies, ranking them by topical relation to the protocol and by the best SJR 2025 journal quartile, not by quality or findings. The kept set therefore differs from the dropped set. Journal quartile: kept 133 Q1 (84.7%), 18 Q2 (11.5%), 5 Q3 (3.2%), 1 unranked (0.6%); dropped 74 Q1 (20.3%), 29 Q2 (8.0%), 18 Q3 (4.9%), 22 Q4 (6.0%), 221 unranked (60.7%). Evidence mix by study type, kept (n=157) vs dropped (n=364): modelling-simulation 78 (49.7%) vs 124 (34.1%); techno-economic-assessment 24 (15.3%) vs 58 (15.9%); empirical-case-study 17 (10.8%) vs 58 (15.9%); review 14 (8.9%) vs 46 (12.6%); other 10 (6.4%) vs 29 (8.0%); qualitative-social-study 9 (5.7%) vs 14 (3.8%); policy-analysis 5 (3.2%) vs 35 (9.6%). The synthesis thus leans toward journals ranked in SJR Q1 and toward model-based studies, and under-represents policy-analysis studies (5 of 40 policy-analysis studies kept) and venues without an SJR quartile such as regional and Spanish-language journals; findings on policy and institutional barriers rest on a smaller evidence base than the full eligible set would give. Mean publication year was 2022.2 for kept and 2021.1 for dropped studies.'})
json.dump(out, open('review/synthesis/evidence/limitations.json', 'w'), ensure_ascii=False, indent=1)
print(len(out))
