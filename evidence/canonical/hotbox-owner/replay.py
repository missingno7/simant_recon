"""Whole-source ownership contrasts for the unadmitted DGROUP:60B0 record.

Matching the initialized contribution does not prove its source owner or role.
Original bytes are comparison input only; drafts are ordinary symbolic C.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import sys

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / 'src/program.json').is_file())
sys.path.insert(0, str(ROOT / 'tools'))
import canonical
import modules
from omf import OmfReader


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def code_projection(obj):
    names = {s['name'] for s in obj.segment_defs
             if str(s.get('class', '')).upper().endswith('CODE')}
    return {name: {
        'bytes': sha(bytes(obj.segments.get(name, b''))),
        'length': obj.segment_lengths[name],
        'fixups': [f for f in obj.linker_fixups if f['segment'] == name],
        'publics': [p for p in obj.publics if p['segment'] == name],
        'local_publics': [p for p in obj.local_publics if p['segment'] == name],
    } for name in sorted(names)}


RECORD = '''
/* Compatible hypothesis only: ownership and activation remain unproved. */
struct {
    struct Rect r;
    int (far *fn)(int, int, unsigned, int, int);
    int code;
    int extra;
    unsigned mouse_mask;
} investigatedMenuHotBox = { { 0, 0, 639, 16 }, f_1B73_030F, 0, 0, 0x0601 };
'''
RECT = 'struct Rect { int left; int top; int right; int bottom; };\n'
CALLBACK = 'extern int far f_1B73_030F(int, int, unsigned, int, int);\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    out = args.out.resolve() if args.out.is_absolute() else (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT / 'build') or out == ROOT / 'build' or out.exists():
        raise ValueError('fresh output directory strictly beneath build required')
    pinned = ('src/program.json', 'layout/manifest.json', 'layout/oracle.lock.json',
              'layout/toolchain.json', 'src/S10/m35F5.c', 'src/S20/m39F1.c',
              'src/root/m1B73.asm', 'src/root/m1FD2.c', 'tools/modules.py',
              'tools/compiler.py', 'tools/match.py', 'tools/omf.py',
              Path(__file__).relative_to(ROOT).as_posix())
    pins = {name: sha((ROOT / name).read_bytes()) for name in pinned}
    man = modules.load_manifest()
    s10, s20 = man['modules']['S10:35F5'], man['modules']['S20:39F1']
    original = (ROOT / s10['source']).read_bytes().decode('latin1')
    if original.count('extern void far f_1B73_030F();') != 1:
        raise ValueError('reviewed callback declaration context changed')
    trailing = original.replace('extern void far f_1B73_030F();',
                                'extern int far f_1B73_030F();') + RECORD
    standalone = RECT + CALLBACK + RECORD.replace('struct {', 'static struct {', 1)
    front = (ROOT / s20['source']).read_bytes().decode('latin1')
    if front.count('static char g_6108 = 0;') != 1:
        raise ValueError('reviewed S20 initializer context changed')
    front = RECT + front.replace('static char g_6108 = 0;',
                               CALLBACK + RECORD + '\nstatic char g_6108 = 0;')
    variants = [('canonical', original, copy.deepcopy(s10)),
                ('s10_trailing', trailing, copy.deepcopy(s10)),
                ('standalone', standalone, {
                    'unit': 'data', 'seg': 0x55B3, 'origin': 0x60B0,
                    'profile': s10['profile'], 'flags': s10['flags'], 'lang': 'c',
                    'placements': {'_DATA': {'seg': 0x55B3, 'off': 0x60B0, 'size': 18}},
                    'link_after': 'S10:35F5'}),
                ('s20_front', front, copy.deepcopy(s20))]
    variants[1][2]['placements']['_DATA']['size'] = 56
    variants[3][2]['placements']['_DATA'] = {'seg': 0x55B3, 'off': 0x60B0, 'size': 151}
    out.mkdir(parents=True)
    results, baseline = {}, None
    for name, text, mod in variants:
        (out / (name + '.c')).write_bytes(text.encode('latin1'))
        collected = {}
        verified = modules.verify_module(text, mod, mod.get('claims', []),
                                         collect=collected, man=man)
        raw = collected['object']
        obj = OmfReader(communals=True).read(raw)
        (out / (name + '.obj')).write_bytes(raw)
        projection = code_projection(obj)
        if name == 'canonical':
            baseline = projection
        results[name] = {
            'source_sha256': sha(text.encode('latin1')), 'object_sha256': sha(raw),
            'accepted_peers': len(mod.get('claims', [])),
            'exact_peers_and_registered_data': verified['exact'],
            'data': verified.get('data'), 'module_reasons': verified.get('module_reasons'),
            'code_projection_sha256': sha(json.dumps(projection, sort_keys=True).encode()),
            'complete_code_projection_equals_canonical': projection == baseline
                if name in ('canonical', 's10_trailing') else None,
            'semantic_definition_unchanged':
                canonical.definition_sha(text, 'o10_35F5_0384') ==
                canonical.definition_sha(original, 'o10_35F5_0384')
                if name in ('canonical', 's10_trailing') else None,
            'data_fixups': [f for f in obj.linker_fixups if f['segment'] == '_DATA'],
        }
    checks = {
        'canonical_peers_and_data': results['canonical']['exact_peers_and_registered_data'],
        'trailing_peers_and_complete_data': results['s10_trailing']['exact_peers_and_registered_data'],
        'trailing_full_code_and_ordered_fixups': results['s10_trailing']['complete_code_projection_equals_canonical'],
        'semantic_body_unchanged': results['s10_trailing']['semantic_definition_unchanged'],
        'separate_contribution_also_matches': results['standalone']['exact_peers_and_registered_data'],
        'front_definition_distinguished': not results['s20_front']['data']['_DATA']['exact'],
        'inputs_unchanged': all(sha((ROOT / name).read_bytes()) == pin for name, pin in pins.items()),
    }
    receipt = {'schema': 'simant-hotbox-ownership-contrasts-v1',
               'passed': all(checks.values()), 'checks': checks, 'input_pins': pins,
               'results': results, 'admitted': False, 'functional_bytes_retained': 18,
               'missing_fact': 'Positive designation of this particular range: registration/copy, '
                               'declaration anchor or independent initializer provenance.',
               'scope': 'Whole-source compatibility controls, not storage or activation acceptance.'}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': receipt['passed'], 'checks': checks, 'out': str(out)}))
    return int(not receipt['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
