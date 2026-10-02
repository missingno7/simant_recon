import json
import sys
from pathlib import Path
sys.path.insert(0, 'tools')
import autosearch
import compilerstate
import idscan
import modctx

name = 'LessonDone'
ctx = modctx.resolve(func=name)
base = autosearch.unscaffold(ctx.text, name)
out = Path('build/workers/hardtail_root/lesson-phase')
out.mkdir(parents=True, exist_ok=True)
base_path = out / 'base.c'
base_path.write_text(base, encoding='latin1')
position = idscan.position(base, top=True)
variants = []
for count in range(17):
    path = out / f'pad-{count:02d}.c'
    path.write_text(idscan.padded(base, position, count), encoding='latin1')
    variants.append({'parameters': {'identifier_count': count, 'position': 'top', 'kind': 'extern'}, 'source': str(path)})
spec = {'function': name, 'base_source': str(base_path), 'dimension': 'CROSS_JUMP_REPRESENTATIVE_PHASE',
        'hypothesis': 'Observed switch CFG retains a different physical representative of duplicate case bodies. Prior body reordering emits identical bytes. Test whether declaration-count phase changes tail-merge representatives or comparison operand order.',
        'diagnostic_only': True, 'prior_controls': ['work/takeover/fleet-lifetimes/fleet_lesson/REPORT.md',
            'work/takeover/residue-controls/lesson_case_groups.py'], 'variants': variants}
(out / 'spec.json').write_text(json.dumps(spec, indent=1))
compilerstate.run(spec, out, Path('build/workers/hardtail_root/experiments-lesson.jsonl'),
                  [Path('work/takeover/hardtail/experiments.jsonl')])
