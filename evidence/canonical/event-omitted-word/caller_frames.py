"""Recompile canonical caller modules and reproduce the omitted-word receipts.

Prints JSON; redirect to an isolated output to compare with caller-frames.json.
Never changes canonical sources, manifests or expected bytes.
"""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'tools'), 'C:/tools/capstone-5.0.3']
import modules
import exe
from omf import OmfReader
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

SITES = {
    'src/window/menu_tracking.c': [
        dict(id='S10-menu-selection', function='menu_track_popup', call_offset='09C0',
             wrapper_bp_0e='caller BP-74h: saved incoming SI', expression='portable_menu_saved_si',
             source_value='menu_track_bar_selection m * 4, captured before popup entry', status='BOUND'),
        dict(id='S10-empty-menu', function='menu_track_popup', call_offset='0A4B',
             wrapper_bp_0e='caller BP-74h: saved incoming SI', expression='portable_menu_saved_si',
             source_value='menu_track_bar_selection m * 4, captured before popup entry', status='BOUND'),
    ],
    'src/ui/game_events.c': [
        dict(id='S19-key-command', function='input_dispatch_game_key', call_offset='02F2',
             wrapper_bp_0e='caller BP-8: saved incoming SI', expression='portable_event_incoming_si',
             source_value='DoEvent current SI: dy after a Ctrl-scroll iteration, otherwise its incoming SI',
             status='BOUND_MAIN_PATH_OPEN_PERIODIC_ENTRY'),
    ],
    'src/startup/main.c': [
        dict(id='main-event-pump', function='main', call_offsets=['02E7','02FD'],
             expression='frames', source_value='register unsigned frames in SI', status='BOUND'),
    ],
    'src/ui/view_dialog_helpers.c': [
        dict(id='edge-scroll-DoEvent', function='ui_pump_events_edge_scroll', call_offset='01F2',
             expression='portable_event_incoming_si', source_value='incoming SI, preserved until DoEvent', status='BOUND'),
        dict(id='periodic-entry', function='ui_pump_events_periodically', call_offset='01B0',
             expression='0', source_value='incoming SI, no local definition and no source references to this entry',
             status='UNBOUND_EXPLICIT_ZERO_NORMALIZATION'),
    ],
}
FUNCTIONS = {
    'src/window/menu_tracking.c': ['menu_track_bar_selection','menu_track_popup'],
    'src/ui/game_events.c': ['DoEvent','input_dispatch_game_key'],
    'src/startup/main.c': ['main'],
    'src/ui/view_dialog_helpers.c': ['ui_pump_events_periodically','ui_pump_events_edge_scroll'],
}

def main():
    manifest = modules.load_manifest()
    rows = []
    for source, sites in SITES.items():
        key, rec = next((k,r) for k,r in manifest['modules'].items() if r['source']==source)
        collected = {}
        proof = modules.verify_module((ROOT/source).read_text(), rec, rec['claims'], collect=collected, man=manifest)
        assert proof['compile_ok'], proof
        assert proof['object_sha256']==rec['object_sha256'], (key,proof['object_sha256'])
        for name in FUNCTIONS[source]:
            assert proof['claims'][name]['exact'], (key,name,proof['claims'][name])
        obj = OmfReader(communals=True).read(collected['object'])
        functions = {}
        for name in FUNCTIONS[source]:
            p = next(p for p in obj.publics if p['name']=='_'+name)
            claim = next(c for c in rec['claims'] if c['name']==name)
            extent = claim['size']
            delta = claim['off'] - p['offset']
            blob = obj.segment_bytes(p['segment'])[p['offset']:p['offset']+extent]
            instructions = []
            for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(blob,claim['off']):
                fixups = [dict(f,offset=f['offset']+delta) for f in obj.fixups_in(p['segment']) if i.address<=f['offset']+delta<i.address+i.size]
                instructions.append(dict(offset=f'{i.address:04X}', bytes=i.bytes.hex(),
                                         asm=(i.mnemonic+' '+i.op_str).strip(), fixups=fixups))
            functions[name] = dict(offset=f'{claim["off"]:04X}', object_offset=f'{p["offset"]:04X}', size=extent,
                                   strict_claim=proof['claims'][name], instructions=instructions)
        rows.append(dict(module=key,source=source,source_sha256=hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),
                         profile=rec['profile'],flags=rec['flags'],object_sha256=proof['object_sha256'],
                         whole_module_exact=proof['exact'],sites=sites,functions=functions))
    # Bind every annotated call to the fresh object's external/local call operand.
    for row in rows:
        for site in row['sites']:
            ins = row['functions'][site['function']]['instructions']
            for offset in site.get('call_offsets',[site.get('call_offset')]):
                i=next((i for i in ins if i['offset']==offset),None)
                assert i is not None, (row['source'],site,ins[0],ins[-1])
                assert i['asm'].startswith(('call ','lcall ')), (site,i)
    # S19 saves SI after __aFchkstk, so check that helper rather than assuming
    # its scratch-register contract. Its successful path allocates AX bytes
    # and returns with SI untouched; the failing branch does not return.
    image=exe.load()
    stack_check=list(Cs(CS_ARCH_X86,CS_MODE_16).disasm(image.read('root',0x29f4*16+0x2cc,36),0x2cc))
    assert all('si' not in i.op_str for i in stack_check)
    runtime=dict(name='__aFchkstk',address='root:29F4:02CC',size=36,
                 oracle_sha256=image.sha256,
                 effect='Successful path: SP -= AX, SI unchanged; failure transfers to runtime error handling.',
                 instructions=[dict(offset=f'{i.address:04X}',asm=(i.mnemonic+' '+i.op_str).strip()) for i in stack_check])
    print(json.dumps(dict(schema='simant-event-caller-frames-v1', modules=rows,runtime_stack_check=runtime),indent=2))

if __name__=='__main__':main()
