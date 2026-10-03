"""Exercise actual central map-center/score bodies with the selected V6 owners."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'portable/tools'))
from whole_program import function_heads
from portable.whole_program.conversions import source_bounded_simulation_state_v6 as selected


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def body(text, name):
    heads = [h for h in function_heads(text) if h['name'] == name]
    if len(heads) != 1:
        raise ValueError(f'central function definition changed: {name}')
    return text[heads[0]['start']:heads[0]['end']]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build/workers'):
        raise ValueError('new scratch directory required')
    gen = ROOT / 'build/workers/whole_program/generated'
    point_path = gen / 'root_m004A.c'
    score_path = gen / 'S14_m384C.c'
    plan = selected.load_plan()
    header, owners = selected.render_owners(plan)
    if (gen / 'simulation_state_50f6.h').read_text() != header or \
            (gen / 'simulation_state_50f6.c').read_text() != owners:
        raise ValueError('central simulation owners differ from fixed plan')
    point_source = point_path.read_text()
    score_source = score_path.read_text()
    for source in (point_source, score_source):
        if '#include "simulation_state_50f6.h"' not in source:
            raise ValueError('central V6 adapter was not selected')
    prefix = '#include <stdint.h>\n#include <stdio.h>\n#include "simulation_state_50f6.h"\n#include "native_owners.h"\n'
    point = prefix + '''typedef struct { int16_t x, y; } Point;
int16_t fd_50F6_0FB6 = 20, fd_50F6_0FFA = 40;
static unsigned updates, resets;
void UpdateEdit(void) { ++updates; }
void f_0250_0ED2(void) { ++resets; }
''' + body(point_source, 'f_004A_02AD') + '''
int main(void) {
    native_sim_state_fd_50F6_0508.xy.x = 100;
    native_sim_state_fd_50F6_0508.xy.y = 200;
    for (int plane = 1; plane <= 3; ++plane) {
        native_state_MapPlane.signed_value = (int16_t)plane;
        f_004A_02AD();
    }
    NativeSimStatePointV6 *centers[3] = {
        &native_sim_state_fd_50F6_0596, &native_sim_state_fd_50F6_06A6,
        &native_sim_state_fd_50F6_072E};
    for (unsigned i = 0; i < 3; ++i)
        if (centers[i]->xy.x != 110 || centers[i]->xy.y != 220 ||
            centers[i]->raw_bytes[0] != 110 || centers[i]->raw_bytes[2] != 220)
            return 1;
    if (updates != 3 || resets != 3) return 2;
    puts("PASS: three source nest-plane center updates use shared point/raw views");
    return 0;
}
'''
    weights = re.search(r'static char weights\[8\]\s*=\s*\{[^}]+\};', score_source)
    if not weights:
        raise ValueError('original CalcScore weights changed')
    score = prefix + '''int16_t fd_3D57_0828 = 4, fd_50F6_0EAC = 1;
uint8_t fd_3D57_00A4[12][16];
''' + weights.group() + '\n' + body(score_source, 'CalcScore') + '''
int main(void) {
    int16_t scores[8] = {0};
    native_state_fd_50F6_04F4.signed_value = 5;
    native_state_fd_50F6_0C26.signed_value = 5000;
    native_state_MeHealth.signed_value = 100;
    for (int i = 0; i < 4; ++i) {
        int k = (1 + i) & 63;
        native_sim_state_fd_50F6_073C.signed_values[k] = (int16_t)(10 * (i + 1));
        native_sim_state_fd_50F6_0626.signed_values[k] = (int16_t)(i + 1);
        native_sim_state_fd_50F6_06AE.signed_values[k] = (int16_t)(2 * (i + 1));
    }
    if (CalcScore(scores) <= 0 || scores[0] != 25 || scores[1] != 33) return 3;
    if (native_sim_state_fd_50F6_073C.raw_bytes[2] != 10 ||
        native_sim_state_fd_50F6_073C.raw_bytes[3] != 0) return 4;
    puts("PASS: original CalcScore reads the selected history/raw owners");
    return 0;
}
'''
    inputs = [Path(__file__), point_path, score_path, gen / 'simulation_state_50f6.h',
        gen / 'simulation_state_50f6.c', gen / 'native_owners.h', gen / 'native_owners.c',
        ROOT / 'portable/whole_program/conversions/source_bounded_simulation_state_v6.py',
        selected.PLAN_PATH]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}
    out.mkdir(parents=True)
    compiler = Path('C:/msys64/mingw64/bin/gcc.exe')
    results = {}
    for name, source in (('point', point), ('score', score)):
        cfile, exe = out / (name + '.c'), out / (name + '.exe')
        cfile.write_text(source)
        command = [str(compiler), '-std=c11', '-Wall', '-Wextra', '-Werror',
            '-Wno-unused-variable',
            '-DSIMANT_NATIVE_LITTLE_ENDIAN=1', '-I', str(gen), str(cfile),
            str(gen / 'simulation_state_50f6.c'), str(gen / 'native_owners.c'), '-o', str(exe)]
        compiled = subprocess.run(command, capture_output=True, text=True)
        if compiled.returncode:
            raise RuntimeError(compiled.stderr)
        ran = subprocess.run([str(exe)], capture_output=True, text=True, timeout=10)
        if ran.returncode:
            raise RuntimeError(f'{name}: exit {ran.returncode} {ran.stderr}')
        results[name] = {'exit': 0, 'stdout': ran.stdout, 'source_sha256': sha(cfile)}
    if before != {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}:
        raise ValueError('native simulation test inputs changed')
    report = {'schema': 'simant-central-simulation-state-v6-v1', 'status': 'PASS',
        'inputs': before, 'compiler_sha256': sha(compiler), 'results': results,
        'claim': 'Actual central source map-center and score consumers use the emitted V6 owners; source callbacks and non-owned score inputs are controlled boundaries',
        'historical_claim': False}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
