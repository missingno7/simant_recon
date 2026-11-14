"""Explicit, source-pinned yard animation identity observation; no game mutation."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
RULE='anim-id-pattern-v1'
ARRAYS={'yard_rain_anim_indices':15,'yard_black_swarm_anim_indices':17,'yard_red_swarm_anim_indices':17}
SCALARS={'g_2A2A':'DrawSimKid','g_2A2C':'DrawSimCat','g_2A2E':'DrawSimBird',
         'g_2A30':'DrawDog','g_2A32':'DrawMower','g_2A34':'DrawForSale',
         'g_2A3E':'DrawSimKid','g_2A40':'DrawAnimYardMessage'}
PREFIX='S13:384C::'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()

def original_scalars():
    """Bind each local from real read AND write instructions, not its name alone."""
    sys.path.insert(0,str(ROOT/'tools'))
    import exe
    from capstone import Cs,CS_ARCH_X86,CS_MODE_16
    from capstone.x86 import X86_OP_MEM,X86_OP_IMM,X86_OP_REG,X86_REG_AX
    module=json.loads((ROOT/'layout/manifest.json').read_text())['modules']['S13:384C']
    decoder=Cs(CS_ARCH_X86,CS_MODE_16);decoder.detail=True
    result={}
    for name,function in SCALARS.items():
        claim=next(c for c in module['claims'] if c.get('name')==function)
        if not claim['provenance'].startswith('EXACT'):raise ValueError('Unproved yard function: '+function)
        code=exe.load().read(claim['unit'],claim['seg']*16+claim['off'],claim['size'])
        reads=set();writes=set()
        for ins in decoder.disasm(code,claim['off']):
            ops=ins.operands
            if len(ops)!=2 or ops[0].type!=X86_OP_MEM or ops[0].size!=2:continue
            memory=ops[0].mem
            if memory.base or memory.index:continue
            if ins.mnemonic=='cmp' and ops[1].type==X86_OP_IMM and ops[1].imm in (-1,65535):reads.add(memory.disp)
            if ins.mnemonic=='mov' and ops[1].type==X86_OP_REG and ops[1].reg==X86_REG_AX:writes.add(memory.disp)
        offset=int(name[2:],16)
        if offset not in reads&writes:raise ValueError('Original holder binding changed: '+name)
        placement=module['placements']['_DATA']
        if not placement['off']<=offset<placement['off']+placement['size']:raise ValueError('Holder outside original data contribution')
        result[PREFIX+name]=placement['seg']*16+offset
    return result

def extend_schema(state):
    """Add the eight previously unbound locals only for this ideal observation."""
    from .state_schema import inventory
    addresses=original_scalars();canonical=inventory()
    for name,address in addresses.items():
        view=state['excluded'][name]
        if view['status']!='OK' or view['bytes']!=2:raise ValueError('Scalar ID native layout changed: '+name)
        state['items'].append(dict(name=name,bytes=2,verdict=True,category='game_state',original_address=address,
            canonical_address=canonical[name]['dos_address'],slices=[[view['address'],2]],sentinel=False))
        del state['excluded'][name]
    stable=[{k:v for k,v in item.items() if k not in ('slices','canonical_address')} for item in state['items']]
    state['identity']=hashlib.sha256(json.dumps(stable,sort_keys=True).encode()).hexdigest()
    # No ID holder may overlap a persistent SaveRec extent on either image.
    names=set(ARRAYS)|set(addresses)
    for item in state['items']:
        if item['name'] not in names:continue
        for save in state['items']:
            if not save['name'].startswith('save:'):continue
            for side in ('original_address','canonical_address'):
                if max(item[side],save[side])<min(item[side]+item['bytes'],save[side]+save['bytes']):
                    raise ValueError('ID holder overlaps SaveRec: '+item['name'])
    return state

def identity_views(state):
    policy=json.loads((HERE/'runtime_views.json').read_text())
    expected=dict(ARRAYS,**{PREFIX+n:1 for n in SCALARS});found={}
    for index,item in enumerate(state['items']):
        name=item['name']
        if name not in expected:continue
        if policy[name].get('ideal_sound_off_observer')!=RULE or item['bytes']!=2*expected[name] or item['sentinel']:
            raise ValueError('Animation identity policy/layout changed: '+name)
        found[name]=dict(index=index,slots=expected[name],bytes=item['bytes'])
    if set(found)!=set(expected):raise ValueError('Missing animation identity holder')
    return found

def identity_receipt(state):
    return dict(contract=RULE,views=identity_views(state),raw_diagnostics=True,
        specification='Per holder: -1 preserved, other valid IDs assigned zero-based ordinals by first appearance; equal IDs share an ordinal; high-bit invalid words retained literally.',
        sources={p:sha(ROOT/p) for p in ('src/graphics/anim.c','src/ui/yard_window.c','src/ui/view_dialog_helpers.c')},
        header_sha256=sha(HERE/'animation_identity.h'),
        evidence='evidence/canonical/native-ideal-clock/animation-identity.md')

def compare_raw(dos,native,views,entries):
    """Retain first raw values/count per holder; every word stays in the sidecar."""
    def read(path):
        values={}
        for line in path.read_text().splitlines():
            step,index,*words=line.split();key=(int(step),int(index))
            if key in values:raise ValueError('Duplicate animation diagnostic row')
            values[key]=[int(v,16) if int(v,16)<32768 else int(v,16)-65536 for v in words]
        return values
    left,right=read(dos),read(native);result={}
    for name,view in views.items():
        first=None;different=0;live=0
        for entry in range(1,entries+1):
            key=(entry,view['index']);a,b=left[key],right[key]
            if len(a)!=view['slots'] or len(b)!=view['slots']:raise ValueError('Truncated animation diagnostic row')
            live+=any(v!=-1 for v in a+b)
            if a!=b:
                different+=1
                if first is None:first=dict(entry=entry,dos=a,native=b)
        result[name]=dict(entries=entries,non_sentinel_entries=live,raw_different_entries=different,first_difference=first)
    if len(right)!=entries*len(views):raise ValueError('Incomplete animation diagnostics')
    return result
