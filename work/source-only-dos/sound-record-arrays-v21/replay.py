"""Replay the admitted research sources into a fresh unadmitted directory."""
from pathlib import Path
import hashlib
import json
import runpy
import uuid

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def main():
    contract=json.loads((ROOT/'work/source-only-dos/sound-record-arrays-contract-v1.json').read_text())
    for identity in (contract['probe_source'], next(p for p in contract['inputs']
            if p['path']=='work/source-only-dos/sound-record-arrays-v21/provider.c')):
        data=(ROOT/identity['path']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=identity['sha256'] or len(data)!=identity['size']:
            raise ValueError('admitted research source drift: '+identity['path'])
    candidate=ROOT/'build/source-only-dos-research/sound-record-arrays'/uuid.uuid4().hex
    namespace=runpy.run_path(str(HERE/'probe.py'),run_name='candidate_probe')
    state=namespace['main'].__globals__
    state.update(ROOT=ROOT,OUT=candidate,PROVIDER_PATH=HERE/'provider.c')
    namespace['main']()
    result=json.loads((candidate/'probe-result.json').read_text())
    if (not result['all_required_checks_pass'] or result['denied_oracle_reads']
            or len(result['fixtures'])!=16
            or sum(row['executed'] is False for row in result['fixtures'])!=2):
        raise ValueError('fresh component replay failed')
    print('Fresh unadmitted component replay PASS:',candidate/'probe-result.json')

if __name__=='__main__':main()
