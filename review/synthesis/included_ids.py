"""Included study ids: extracted studies minus those whose final full-text decision is exclude
(e.g. E7 exclusions applied after extraction, amendment 3)."""
import json

def included():
    ex = {json.loads(l)['record_id'] for l in open('review/extraction.jsonl')}
    last = {}
    for l in open('review/screening.jsonl'):
        r = json.loads(l)
        if r['stage'] == 'ft' and r.get('final'):
            last[r['record_id']] = r['decision']
    return sorted(i for i in ex if last.get(i, 'include') == 'include')
