"""Supported exclusion of the two known computed critical-selector aliases."""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
sys.path.insert(0, str(ROOT/'tools'))
import behavior as b, resource_domains
if not __debug__:
    raise RuntimeError('proof checks require Python without -O')

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def support():
    module = load('critical_inventory', 'evidence/canonical/icon-handle-view/vga_probe.py')
    # g_8DFC is used by the reviewed SONGP macro; whole-source pins bind that
    # macro and its segment writes without weakening the macro escape guard.
    module.TARGETS = {'g_8CCB', 'g_8CF2', 'g_8DD8', 'g_8DFE',
                      'g_7566', 'f_1C62_06A6', 'f_208F_058B', 'f_284A_0199',
                      'f_284A_0256', 'win_UnlockWin', 'f_23AE_0069'}
    return module

PROTECTED = {'g_8CCB': 1, 'g_8CF2': 180, 'g_8DD8': 36, 'g_7566': 2,
             'g_8DFC': 2, 'g_8DFE': 4}

def save_ranges(texts, raw=None):
    db = load('critical_save', 'evidence/canonical/database-domain/replay.py')
    db.save_table_proof(texts)
    if raw is None:
        raw = db.oracle_machine('OpenDB').read(b.symbol_address('fd_4E4B_0000'), 308*8)
    for i in range(307):
        size, count, off, seg = struct.unpack_from('<HHHH', raw, i*8)
        start = seg*16+off
        for name, width in PROTECTED.items():
            at = protected_address(name)
            if start < at+width and at < start+size*count:
                raise ValueError('save overlaps critical selector/count/views: '+name)
    return dict(records=307, descriptor_sha256=hashlib.sha256(raw).hexdigest(),
                protected=PROTECTED, intersections=0)

def protected_address(name):
    # Private cache displacement is retained in the exact root:23AE stores.
    if name == 'g_8CF2':
        return b.symbol('g_8CCB')['seg']*16+0x8cf2
    return b.symbol_address(name)

def songs():
    corpus = resource_domains.collect()['corpus']
    parser = resource_domains.decoder()
    rows = parser.parse_records('SOUND')[1]
    meta = [r for r in rows if r['kind'] == 18]
    streams = {r['id']: r for r in rows if r['kind'] == 20}
    references = {struct.unpack_from('>H', r['payload'])[0] for r in meta}
    if references != set(streams):
        raise ValueError('song metadata and streams no longer form a closed set')
    counts = {str(i): parser.parse_smf(r['payload'])['header_track_count']
              for i, r in sorted(streams.items())}
    calls, _ = parser.song_call_sites({r['id'] for r in meta})
    return dict(corpus=corpus, metadata=len(meta), streams=len(streams),
                track_counts=counts, calls=calls)

def collect():
    shared = support()
    texts, program, registry = shared.inventory()
    ids = load('critical_ids', 'evidence/canonical/window-domain/handle_ids_guard.py').check()
    expected_ids = json.loads((ROOT/'evidence/canonical/window-domain/handle-id-facts.json').read_text())
    if ids != expected_ids:
        raise ValueError('window ID proof changed')
    song = songs()
    assert len(song['calls']) == 36 and (song['metadata'], song['streams']) == (33, 30)
    assert (min(song['track_counts'].values()), max(song['track_counts'].values())) == (2, 10)
    controls = [original_store(n) for n in (10, 32633, 32634)]
    assert [r['original_instructions_changed_selector'] for r in controls] == [False, False, True]
    return dict(schema='simant-critical-selector-domain-v1',
        scope='Known window-cache and MIDI-offset aliases only; no global deadness, constant substitution or corruption-immunity claim.',
        inventory=shared.inventory_pins(texts, program, registry),
        census=shared.census(texts, program, registry), save_ranges=save_ranges(texts),
        window_ids=ids, songs=song, original_song_store_controls=controls,
        alias_arithmetic={'window_index': -10, 'first_song_index': 32633,
                          'minimum_song_count': 32634})

def check():
    result = collect()
    if result != json.loads(Path(__file__).with_name('selector-facts.json').read_text()):
        raise ValueError('critical-selector proof differs from reviewed facts')
    return result


from types import SimpleNamespace
import exe, functions

def original_store(count):
    x = exe.load()
    machine = b.Machine(SimpleNamespace(
        function=functions.get('f_284A_0199'),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in x.vectors},
    ))
    offset_owner = b.symbol_address('g_8DD8')
    selector = b.symbol_address('g_8CCB')
    song_segment = 0x7100
    writes = [
        (b.symbol_address('g_8DFC'), b.words(song_segment)),
        (song_segment * 16, bytes(0x10000)),
        (selector, b'\x5a'),
    ]
    machine.run(b.Case(
        # The first out-of-bounds word at g_8DD8[18] aliases g_8DFC. Choose
        # off=7068h so that this store writes back the fixture segment 7100h;
        # this isolates the later wrapped store from an accidental pointer fault.
        f'original-song-track-count-{count}', args=[count, 0x7068], writes=writes,
        # A separate test stack prevents this deliberately out-of-domain walk
        # from corrupting its own live return frame before the wrapped address.
        registers={'ss': 0x9000},
        return_kind='void', max_instructions=10_000_000, max_blocks=5_000_000,
    ))
    touched = machine.read(selector, 1)[0]
    return {
        'count': count,
        'track_offsets_base': f'{offset_owner:05X}',
        'selector_address': f'{selector:05X}',
        'selector_initial': '5A',
        'selector_after': f'{touched:02X}',
        'original_instructions_changed_selector': touched != 0x5a,
        'blocks': machine.blocks,
    }


if __name__ == '__main__':
    check(); print('PASS: critical selector known aliases excluded in supported domain')
