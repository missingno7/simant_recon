"""Compare fingerprints from explicit repeat recordings of the same DOS EXE."""
import argparse
import json
from pathlib import Path
try:
    from .step_state import read_hashes
except ImportError:
    from step_state import read_hashes


def compare(first, repeat):
    manifests=[json.loads((p/'manifest.json').read_text()) for p in (first,repeat)]
    if any(m.get('input_contract')!='service-samples-v5' for m in manifests):
        raise ValueError('Repeat requires service-samples-v5; v4 timing is refused')
    for key in ('keyboard_layout','input_contract','executable_sha256','scenario_sha256','script_sha256','schema_identity','steps'):
        if manifests[0][key]!=manifests[1][key]:raise ValueError('Repeat identity differs: '+key)
    if not all(m.get('complete') for m in manifests):raise ValueError('Repeat capture is incomplete')
    state=json.loads((first/'schema.json').read_text());items=state['items']
    rows=[read_hashes(p/'capture/observer.txt.hash',len(items)) for p in (first,repeat)]
    if any(len(r)!=m['steps'] for r,m in zip(rows,manifests)):raise ValueError('Repeat fingerprint count differs from manifest')
    game=[];separate={}
    for step,(a,b) in enumerate(zip(*rows),1):
        for item,x,y in zip(items,a,b):
            if x==y:continue
            row=dict(step=step,name=item['name'],hashes=[x,y])
            if item['verdict']:game.append(row)
            else:separate.setdefault(item['name'],row)
        if game:break
    return dict(verdict='ORIGINAL_DOS_NONDETERMINISTIC' if game else 'ORIGINAL_EQUAL_ALL',
                steps_compared=game[0]['step'] if game else len(rows[0]),
                game_differences=game,separate_differences=separate)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('first',type=Path);ap.add_argument('repeat',type=Path);ap.add_argument('--out',type=Path)
    a=ap.parse_args();result=compare(a.first,a.repeat)
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
