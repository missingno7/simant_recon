"""Fresh parent whole-TU verification of the three bounded negative results."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import modctx
import modules
import variants

OUT = Path(__file__).resolve().parent / 'forensics-fresh'
OUT.mkdir(exist_ok=True)
compiler.WORK = OUT / 'cc'
compiler.WORK.mkdir(exist_ok=True)
WORKER = ROOT / 'build/workers/dos_historical_residue_forensics_v32'
index = json.loads((WORKER / 'stable-artifacts.json').read_bytes())
assert index['authority_unchanged'] and index['new_families'] == 0
assert index['expansion'] == 'NONE' and index['fresh_compiles'] == 12
for pin in index['artifacts']:
    raw = Path(pin['path']).read_bytes()
    assert len(raw) == pin['size']
    assert hashlib.sha256(raw).hexdigest() == pin['sha256'], pin['path']
rows = []
for name, extent, differences, peers in (
        ('o15_384C_0239', 326, 2, 7), ('FindIndex', 267, 3, 6),
        ('f_171C_0CF4', 490, 6, 57)):
    context = modctx.resolve(func=name)
    folder = WORKER / name
    text = (folder / 'module.c').read_text(encoding='latin1')
    collected = {}
    verdict = modules.verify_module(text, context.module_dict(),
        variants.check_set(context, [name], claims_only=True, text=text), collect=collected)
    assert collected['object'] == (folder / 'module.obj').read_bytes()
    assert collected['object'] == (folder / 'listing-module.obj').read_bytes()
    (OUT / (name + '.obj')).write_bytes(collected['object'])
    (OUT / (name + '-verdict.json')).write_bytes((json.dumps(verdict, indent=2) + '\n').encode())
    assert not verdict['exact'] and not verdict['claims'][name]['exact']
    accepted_peers = [r for n, r in verdict['claims'].items() if n != name]
    assert len(accepted_peers) == peers and all(r['exact'] for r in accepted_peers)
    assert all(r['exact'] for r in verdict['data'].values())
    residue = json.loads((folder / 'instruction-residue.json').read_bytes())
    obj = modctx.read_obj(collected['object'])
    bound, _ = modctx.bind_function(context, obj, context.function(name))
    diffs = [i for i, (a, b) in enumerate(zip(bound.candidate, bound.original)) if a != b]
    assert len(bound.candidate) == len(bound.original) == extent
    assert len(diffs) == differences and diffs == [r['relative'] for r in residue['differing_bytes']]
    assert not bound.unbound and sorted(bound.relocs_candidate) == sorted(bound.relocs_expected)
    rows.append(dict(target=name, extent=extent, differing_bytes=differences,
        accepted_peers=peers, private_data='PASS', fixups_and_relocations='PASS',
        fresh_object_identical=True, conclusion='NO_NEW_HYPOTHESIS_OR_EXACT_CANDIDATE'))
print(json.dumps(dict(status='PASS', worker_artifacts_reopened=len(index['artifacts']),
    fresh_parent_whole_TU_compiles=3, targets=rows, promotion=False), indent=2))
