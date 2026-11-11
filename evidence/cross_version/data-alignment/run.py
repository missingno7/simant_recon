"""Reproduce the published DOS/Win16 data-name evidence into fresh build/scratch output.

Run from the repository root:
    python evidence/cross_version/data-alignment/run.py build/scratch/data-alignment

The package is read only during reproduction. Published artifacts are read only
after inference finishes, for comparison; no generated intermediate is an input.
"""
import sys
sys.dont_write_bytecode = True

from pathlib import Path

# All external data inputs. No Win16 tools, sources, disassembly cards or caches
# are read: code, CFGs and loader fixups are regenerated from these two files.
WIN16_ROOT = Path('D:/Prog/simantw_recon')
WIN16_EXE = WIN16_ROOT / 'assets/SIMANTW.EXE'  # Original NE bytes and relocation chains.
WIN16_INVENTORY = WIN16_ROOT / 'evidence/symbols/inventory.json'  # Original publics and code bounds.

# Software dependency used for both 16-bit instruction decoders.
CAPSTONE_DIRECTORY = Path('C:/tools/capstone-5.0.3')
CAPSTONE_VERSION = '5.0.3'
if CAPSTONE_DIRECTORY.exists():
    sys.path.insert(0, str(CAPSTONE_DIRECTORY))

import argparse
import hashlib
import json
import platform
import time
import capstone

import binary
import alignment
import reporting
import data_kinds

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
DOS_EXE = ROOT / 'assets/SIMANT.EXE'
DOS_FUNCTIONS = ROOT / 'layout/functions.json'
DOS_SYMBOLS = ROOT / 'layout/symbols.json'
DECISIONS = ROOT / 'evidence/cross_version/decisions.json'

# Current publication includes all function reviews dated 2026-11-11.
# The digest makes a later cohort change explicit rather than silently changing
# the population behind the published calibration and reference counts.
PAIR_REVIEW_CUTOFF = '2026-11-11'
PAIR_COHORT_SHA256 = '1bb46b8ad41a303ee7d6dbd65a375869ee153653f8927e109e360a999758fea4'
DOS_SHA256 = 'aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11'
WIN16_SHA256 = '538fed3f0fd60a6528a5e5b20990361ac4d274c58266a81e71c24f751612589d'


def write_json(path, value):
    """Write one generated receipt; callers supply a validated output directory."""
    # Git stores this package with LF endings. Explicit LF also makes byte-level
    # reproduction stable after checkout on Windows and on other hosts.
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def main():
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out', type=Path, help='fresh directory strictly below build/scratch')
    args = parser.parse_args()
    output = args.out.resolve()
    scratch = (ROOT / 'build/scratch').resolve()
    if output == scratch or not output.is_relative_to(scratch) or output.exists():
        parser.error('output must be a fresh directory strictly below build/scratch')
    if capstone.__version__ != CAPSTONE_VERSION:
        parser.error(f'Capstone {CAPSTONE_VERSION} is required; found {capstone.__version__}')

    inputs = {}

    def read(path):
        contents = path.read_bytes()
        inputs[str(path)] = {'bytes': len(contents), 'sha256': hashlib.sha256(contents).hexdigest()}
        return contents

    dos_raw, win_raw = read(DOS_EXE), read(WIN16_EXE)
    if hashlib.sha256(dos_raw).hexdigest() != DOS_SHA256 or hashlib.sha256(win_raw).hexdigest() != WIN16_SHA256:
        parser.error('original executable hash mismatch')
    inventory = json.loads(read(WIN16_INVENTORY))
    if inventory['exe_sha256'] != WIN16_SHA256:
        parser.error('Win16 symbol inventory belongs to a different executable')
    symbols = json.loads(read(DOS_SYMBOLS))
    functions = json.loads(read(DOS_FUNCTIONS))
    decisions = json.loads(read(DECISIONS))
    data = binary.Data(dos_raw, win_raw, inventory, symbols)
    data.functions = functions['functions']
    data_kinds.check_transfers(data)
    print('Regenerating Win16 disassembly and control-flow tables...', flush=True)
    data.cards = binary.function_cards(win_raw, data.ne, inventory)
    data.pairs = binary.function_pairs(functions, symbols, decisions, data.cards, PAIR_REVIEW_CUTOFF)
    cohort_hash = hashlib.sha256(json.dumps(data.pairs, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if cohort_hash != PAIR_COHORT_SHA256:
        parser.error(f'function-pair cohort changed: {len(data.pairs)} pairs, digest {cohort_hash}; review scope explicitly')
    print(f'Function-pair cohort: {len(data.pairs)}; review cutoff {PAIR_REVIEW_CUTOFF}', flush=True)
    references, statistics = binary.extract_references(data, functions, data.pairs, data.cards)
    tables = alignment.discover_tables(data)
    print('Following whole stored values and Windows import uses...', flush=True)
    flows = data_kinds.collect_value_flows(data)
    platform_objects = data_kinds.platform_observations(data)
    data.platform_objects = platform_objects
    output.mkdir(parents=True)
    write_json(output / 'inputs.json', {
        'files': inputs, 'python': platform.python_version(), 'capstone': capstone.__version__,
        'review_cutoff': PAIR_REVIEW_CUTOFF, 'cohort_sha256': cohort_hash,
        'code': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PACKAGE.glob('*.py'))},
    })
    write_json(output / 'function-pairs.json', data.pairs)
    write_json(output / 'references.json', references)
    write_json(output / 'extraction-statistics.json', statistics)
    write_json(output / 'tables.json', tables)
    write_json(output / 'value-flows.json', flows)
    write_json(output / 'windows-import-uses.json', platform_objects)

    documents = {}
    calibration = []
    for blind in (True, False):
        suffix = '-blind' if blind else ''
        rows, detail = alignment.match_order(data, references, tables, blind)
        doc = {'matches': rows, 'summary': detail}
        stages = [('order', doc)]
        doc = alignment.add_layout(data, doc, references)
        stages.append(('layout', doc))
        doc = alignment.verify_pointers(data, doc, references)
        stages.append(('pointers', doc))
        doc = alignment.infer_bases(data, doc)
        stages.append(('bases', doc))
        doc = alignment.terminal_gaps(data, doc, references)
        stages.append(('terminal-gaps', doc))
        doc = alignment.terminal_usage(data, doc, references)
        stages.append(('terminal-usage', doc))
        doc = data_kinds.add_value_flows(data, doc, flows, references)
        stages.append(('value-flows', doc))
        doc = data_kinds.add_interior_contents(data, doc, references)
        doc = data_kinds.add_text_tables(data, doc, references)
        saved = {k:v for k,v in doc.items() if k in ('rejected','flow_conflicts')}
        doc = alignment.add_layout(data, doc, references)
        doc.update(saved)
        stages.append(('interior-contents', doc))
        doc = data_kinds.add_layout_contents(data, doc, references)
        stages.append(('layout-contents', doc))
        doc = data_kinds.add_indexed_order(data, doc, references, tables, blind)
        stages.append(('indexed-order', doc))
        for name, stage in stages:
            write_json(output / (name + suffix + '.json'), stage)
            calibration.append({'stage': name + suffix, **alignment.calibrate(stage['matches'], data)})
        documents[blind] = doc

    rows, summary, sizes, rejected = reporting.prepare(data, documents[False], documents[True], references)
    coverage = reporting.coverage(data, rows, references, platform_objects)
    for name, value in [('matches.json', rows), ('object-sizes.json', sizes),
                        ('rejected.json', rejected), ('coverage.json', coverage),
                        ('summary.json', summary), ('calibration.json', calibration)]:
        write_json(output / name, value)

    # Published files are comparison targets, never seeds or inference inputs.
    comparisons = {}
    byte_comparisons = {}
    for name in ('matches.json', 'object-sizes.json', 'rejected.json', 'coverage.json'):
        comparisons[name] = json.loads((output / name).read_text(encoding='utf-8')) == json.loads((PACKAGE / name).read_text(encoding='utf-8'))
        byte_comparisons[name] = (output / name).read_bytes() == (PACKAGE / name).read_bytes()
    elapsed = time.perf_counter() - started
    result = {
        'equal': all(comparisons.values()) and all(byte_comparisons.values()),
        'comparisons': comparisons,
        'byte_comparisons': byte_comparisons,
        'wall_seconds': elapsed,
    }
    write_json(output / 'reproduction.json', result)
    print(f"Published rows: {'EQUAL' if comparisons['matches.json'] else 'DIFFERENT'} ({len(rows)} rows)")
    print('Object sizes:', 'EQUAL' if comparisons['object-sizes.json'] else 'DIFFERENT')
    print('Rejections:', 'EQUAL' if comparisons['rejected.json'] else 'DIFFERENT')
    print('Coverage:', 'EQUAL' if comparisons['coverage.json'] else 'DIFFERENT')
    print('Published artifacts byte-for-byte:', 'EQUAL' if all(byte_comparisons.values()) else 'DIFFERENT')
    print(f'Wall time: {elapsed:.3f} seconds')
    c = summary['published_blind_calibration']
    print(f"Blind calibration: {c['correct']} correct / {c['wrong']} wrong / {c['missed']} missed; {c['steals']} stolen")
    if not result['equal'] or c['wrong'] or c['steals']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
