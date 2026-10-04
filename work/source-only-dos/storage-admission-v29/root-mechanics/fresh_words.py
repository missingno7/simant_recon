"""Fresh root-owned typed FAR word definitions; no original bytes."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import dos_source_bindings as bindings
from omf import OmfReader
from reopen_screen import pin

def main():
    module = 'source-owned:remaining-far-state-words'
    directory = Path(__file__).parent / 'fresh-words'
    directory.mkdir(exist_ok=True)
    text = '\n'.join('int far fd_50F6_' + suffix + ';' for suffix in ('04C0', '0B20', '0F38', '0FB6', '0FFA')) + '\n'
    source = directory / 'remaining-far-state-words.c'
    source.write_bytes(text.encode('ascii'))
    provider = dict(module=module, basename='FARW29', owner=None, profile='msc600ax',
        flags=['/AL', '/Os', '/Gs'], source=pin(source), communals=bindings.provider_communals(module))
    bindings.review_provider_source(text, provider, json.loads((ROOT / 'layout/symbols.json').read_bytes()))
    result = compiler.compile_c(text, 'msc600ax', provider['flags'], basename='FARW29', keep=True)
    log = directory / 'compile.log'
    log.write_bytes(result.log.encode('latin1'))
    assert result.ok, result.log
    path = directory / 'FARW29.OBJ'
    path.write_bytes(result.obj)
    obj = OmfReader(communals=True).read(result.obj)
    proof = bindings.verify_provider(obj, provider)
    report = dict(provider=provider, verification=proof, object=pin(path), compiler_log=pin(log),
        segments=obj.segment_defs, groups=obj.groups, original_executable_used=False)
    (directory / 'compile-receipt.json').write_bytes((json.dumps(report, indent=2) + '\n').encode())
    print('FRESH FAR WORD OWNER PASS: five mutable signed 2-byte commons, no code or initializer')

if __name__ == '__main__':
    main()
