"""Focused live-artifact regression: original clock inputs correct the world seeds.

python portable/tests/acceptance/verify_alignment.py REPLAY_DIR CONTROL_DIR
The control must use the same executable, inputs and poll quantum, without a tape.
"""
import argparse,json
from pathlib import Path


def verify(replayed,control):
    a=json.loads((replayed/'acceptance.json').read_text())
    b=json.loads((control/'acceptance.json').read_text())
    for key in ('executable_sha256','scenario_sha256','script_sha256','dos_executable_sha256','poll_ns'):
        if a['run'][key]!=b['run'][key]: raise ValueError('Regression control identity differs: '+key)
    if not a['run'].get('clock_inputs') or b['run'].get('clock_inputs'):
        raise ValueError('Regression needs a taped run and an untaped control')
    samples={}
    for label,run in [('replayed',a),('control',b)]:
        row=run['steps']['checkpoints']['1']
        seeds=row['three_way']['symbols']['YMapSeeds']
        samples[label]=dict(alignment=row['alignment']['status'],verdict=seeds['verdict'],
                            differing_bytes=seeds['original_vs_native'].get('differing_bytes',0))
        if seeds['original_vs_canonical']['status']!='EQUAL': raise ValueError('DOS world seed premise failed')
    if samples['replayed']['verdict']!='ORIGINAL_EQUAL_ALL' or samples['control']['verdict']!='PORT_INTRODUCED':
        raise ValueError('Original seed replay positive/negative control failed')
    return dict(status='PASS',scope='384 world-seed bytes only; input and timing limitations retained',samples=samples)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('replayed',type=Path);ap.add_argument('control',type=Path)
    args=ap.parse_args();result=verify(args.replayed,args.control)
    (args.replayed/'alignment-regression.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
