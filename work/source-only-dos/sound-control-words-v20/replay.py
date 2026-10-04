"""Replay the pinned research probe into a fresh, unadmitted output directory."""
from pathlib import Path
import hashlib
import json
import runpy
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    admitted = ROOT / 'work/source-only-dos/sound-control-words-contract-v1.json'
    contract = json.loads(admitted.read_text(encoding='utf-8'))
    for identity in (contract['probe_source'], next(p for p in contract['inputs']
            if p['path'] == 'work/source-only-dos/sound-control-words-v20/provider.c')):
        data = (ROOT / identity['path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != identity['sha256'] or len(data) != identity['size']:
            raise ValueError('admitted research source drift: ' + identity['path'])
    candidate = ROOT / 'build/source-only-dos-research/sound-control-words' / uuid.uuid4().hex
    candidate.mkdir(parents=True, exist_ok=False)
    namespace = runpy.run_path(str(HERE / 'probe.py'), run_name='candidate_probe')
    state = namespace['main'].__globals__
    state.update(ROOT=ROOT, OUT=candidate, RUNTIME=candidate / 'runtime',
                 FIXTURES=candidate / 'runtime/fixtures', REPORT=candidate / 'runtime/probe-v20.json',
                 PROVIDER=HERE / 'provider.c')
    namespace['main']()
    result = json.loads(state['REPORT'].read_text(encoding='utf-8'))
    if (not result['runtime']['all_expected_outcomes_pass'] or result['denied_oracle_reads']
            or len(result['runtime']['cases']) != 10):
        raise ValueError('fresh component replay failed')
    print('Fresh unadmitted component replay PASS:', state['REPORT'])


if __name__ == '__main__':
    main()
