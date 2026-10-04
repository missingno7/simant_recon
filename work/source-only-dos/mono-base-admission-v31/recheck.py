"""Read-only audit of the shipped mono-reference admission and installed tools."""
from pathlib import Path
import json
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/manifest.json').is_file())
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import dos_mono_base as policy

def main():
    packet = json.loads((ROOT / 'work/source-only-dos/mono-base-bindings-v1.json').read_bytes())
    c = json.loads(policy.read_pin(packet['runtime_contract']))
    manifest = json.loads((ROOT / 'layout/manifest.json').read_bytes())
    symbols = json.loads((ROOT / 'layout/symbols.json').read_bytes())
    binding = packet['bindings'][0]
    policy.review(binding, manifest['modules']['S01:328E'], symbols)
    report = dict(translation_units=[dict(module='S01:328E', source_binding=binding)],
                  mono_base_contract=c, runtime_components=list(manifest['runtime']['libraries'].values()))
    for name in ('rtlink400', 'rtlink610'):
        policy.require_contract(report, name, compiler.toolchain()['linkers'][name])
    print('MONO BASE RECHECK PASS:', len(c['inputs']), 'pinned inputs; both linkers; no owner extent or game execution')

if __name__ == '__main__': main()
