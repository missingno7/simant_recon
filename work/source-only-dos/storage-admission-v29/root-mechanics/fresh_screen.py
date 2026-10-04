"""Compile the root-owned natural initializer and retain complete proof."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import dos_source_bindings as bindings
from omf import OmfReader
from reopen_screen import pin

SOURCE = '''/* Functional screen clip list; historical TU/order/placement unclaimed. */
struct Rect { int left; int top; int right; int bottom; };
#define RECT_END ((int)0x8000)
struct Rect near g_5A9C[2] = {
    { 0, 0, 349, 639 },
    { RECT_END, RECT_END, RECT_END, RECT_END }
};
'''

def main():
    directory = Path(__file__).parent / 'fresh-screen'
    directory.mkdir(exist_ok=True)
    source = directory / 'screen-clip-list.c'
    source.write_bytes(SOURCE.encode('ascii'))
    provider = dict(module='source-owned:screen-clip-list', basename='SCRLIST', owner=None,
        profile='msc600ax', flags=['/AL', '/Os', '/Gs'], source=pin(source), communals=[],
        storage_kind='initialized_storage', recipe='typed_screen_and_sentinel',
        public_DATA=bindings.initialized_publics('source-owned:screen-clip-list'))
    symbols = json.loads((ROOT / 'layout/symbols.json').read_bytes())
    bindings.review_provider_source(SOURCE, provider, symbols)
    result = compiler.compile_c(SOURCE, provider['profile'], provider['flags'], basename='SCRLIST', keep=True)
    (directory / 'compile.log').write_bytes(result.log.encode('latin1'))
    assert result.ok, result.log
    obj_path = directory / 'SCRLIST.OBJ'
    obj_path.write_bytes(result.obj)
    obj = OmfReader(communals=True).read(result.obj)
    proof = bindings.verify_provider(obj, provider)
    report = dict(provider=provider, verification=proof, object=pin(obj_path),
        compiler_log=pin(directory / 'compile.log'), segments=obj.segment_defs, groups=obj.groups,
        original_executable_used=False)
    (directory / 'compile-receipt.json').write_bytes((json.dumps(report, indent=2) + '\n').encode())
    print('FRESH SCREEN OWNER PASS: 16 initialized bytes, no imports, fixups or code')

if __name__ == '__main__':
    main()
