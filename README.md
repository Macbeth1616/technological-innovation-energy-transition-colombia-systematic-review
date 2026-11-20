# Technological innovation for the energy transition in Colombia, 2015–2025: a systematic review and scientometric analysis

Data and code supporting the systematic review (PRISMA 2020). The review searched Scopus (2026-11-16) and OpenAlex (2026-11-17) for 2015–2025 studies in English or Spanish; 157 reports of 156 studies were included.

## Contents (`review/`)

| File | Content |
|---|---|
| `protocol.json`, `protocol.lock.json` | Protocol, eligibility criteria I1–I5 and E1–E8, and its four dated amendments |
| `searches.jsonl`, `scope.json`, `scope-runs/` | Search strings, dates and result counts |
| `records.jsonl` | Bibliographic metadata of every identified record (abstracts removed) |
| `screening.jsonl` | Title/abstract and full-text decisions, reviewer and exclusion reason |
| `prisma.json` | PRISMA 2020 flow counts |
| `prioritization.json` | Reference-budget ranking behind criterion E8 |
| `ft-availability.jsonl` | Full-text retrieval outcome per report |
| `extraction-plan.csv`, `extraction.jsonl` | Extraction plan and extracted data, each value with a verbatim supporting quote |
| `appraisal.jsonl` | Quality appraisal (adapted Kitchenham and Charters checklist, QA1–QA5) |
| `biblio.json` | Scientometric data |
| `synthesis/` | Codebooks, coded barriers, enablers and impacts, summary data, the scripts that build every table, and the tables as CSV |

Full texts of the included studies are not distributed, as they are under the publishers' copyright; every study is identified by its DOI in `records.jsonl` and in the paper's reference list. The raw Scopus export is likewise not redistributed.

## Licence

Data: CC BY 4.0. Code (`review/synthesis/*.py`): MIT.
