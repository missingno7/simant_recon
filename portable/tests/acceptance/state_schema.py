"""Source/MAP-derived state schema and independent original address anchors."""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
ROOT = TOOL_DIR.parents[2]
sys.path.insert(0,str(ROOT))
from dos import acceptance
if __package__:
    from .canonical_dos_layout import canonical_layout
else:
    from canonical_dos_layout import canonical_layout

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def original_layout(root=ROOT):
    # These are original-image symbol anchors, never canonical MAP placements.
    return {name:dict(dos_address=spec['seg']*16+spec['off'],
                      address_evidence='layout/symbols.json:data:'+name)
            for name,spec in json.loads((root/'layout/symbols.json').read_text())['data'].items()}



def inventory(project=ROOT, oracle_root=ROOT, dos_report=None, native_build=None):
    if len({sha(p/'src/program.json') for p in (project,oracle_root,ROOT)})!=1:
        raise ValueError('canonical program inventories differ; no cross-generation observation')
    program = json.loads((project/'src/program.json').read_text())
    symbols, errors = canonical_layout(oracle_root,dos_report or oracle_root/'build/current/dos/build-report.json')
    if errors: raise ValueError('unresolved canonical DOS data placement: '+str(errors))
    aliases = {s['alias'].lstrip('_@'):s for s in program['aliases'] if s['kind']!='code'}
    lengths = {}
    for module in program['modules']:
        for c in module.get('storage_contract',{}).get('communals',[]):
            lengths[c['name'].lstrip('_@')] = c['length']
    result = {}
    for name, spec in sorted(symbols.items()):
        item = dict(spec)
        if '::' in name and not item.get('native_expr'):
            item['native_file']=re.sub(r'[:@]','_',spec['module'])+'.c'
        if name in aliases:
            alias = aliases[name]
            item.update(owner=alias.get('target',alias.get('owner')).lstrip('_@'),offset=alias.get('offset',0))
        if name in lengths: item.setdefault('bytes',lengths[name])
        result[name] = item
    for name,alias in aliases.items():
        target=alias.get('target',alias.get('owner')).lstrip('_@')
        if name not in result and target in result:
            item=dict(result[target],owner=target,offset=alias.get('offset',0))
            item['dos_address']+=alias.get('offset',0)
            item['address_evidence']='src/program.json reviewed alias + canonical target address'
            if alias.get('view',{}).get('DOS_view_extent_bytes') is not None:
                item['bytes']=alias['view']['DOS_view_extent_bytes']
            result[name]=item
    if native_build is not None:
        facts_path=Path(native_build)/'asm-data-facts.json'
        if facts_path.is_file():
            facts=json.loads(facts_path.read_text())
            text_owner=next((row for row in facts['numeric']
                             if row.get('name')=='text_bitmap_pixels'),None)
            if text_owner is not None:
                for alias,view in (('text_bitmap_string_copy','string'),('g_5F1D','terminator')):
                    if alias in result and view in text_owner['alias_layout']:
                        source_view=text_owner['alias_layout'][view]
                        result[alias].update(owner='text_bitmap_pixels',offset=source_view['offset'],
                                             bytes=source_view['count'],
                                             native_file='canonical_asm_numeric_data.c',
                                             address_evidence='canonical ASM text_bitmap_pixels generated interior view + typed native owner')
    return result

def differences(a,b):
    if len(a)!=len(b): return dict(status='SIZE_MISMATCH',sizes=[len(a),len(b)])
    positions=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    if not positions: return dict(status='EQUAL',bytes=len(a))
    first=positions[0]
    result=dict(status='DIFFERS',bytes=len(a),differing_bytes=len(positions),
                first_offset=first,dos_byte=a[first],native_byte=b[first],
                max_byte_delta=max(abs(a[i]-b[i]) for i in positions),
                examples=[dict(offset=i,dos=a[i],native=b[i]) for i in positions[:8]])
    if len(a) in (1,2,4):
        da,nb=int.from_bytes(a,'little'),int.from_bytes(b,'little')
        result.update(dos_unsigned=da,native_unsigned=nb,unsigned_delta=nb-da)
    return result

def memory_base(memory,addresses):
    hits=[m.start() for m in re.finditer(re.escape(acceptance.SCREEN_CLIP_PATTERN),memory)]
    bases={h-addresses['gfx_screen_clip_list'] for h in hits}
    if len(bases)!=1: raise ValueError('nonunique canonical DOS runtime base: '+str(bases))
    return bases.pop()

