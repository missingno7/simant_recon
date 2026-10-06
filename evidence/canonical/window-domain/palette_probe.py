"""Proposed bounded shipped-window palette proof; metadata only."""
from pathlib import Path
from types import SimpleNamespace
import argparse
import hashlib
import importlib.util
import json
import re
import struct
import sys
sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
sys.path.insert(0, str(ROOT/'tools'))
import behavior as b
import csrc
import exe
import functions
import resource_domains as r
if not __debug__: raise RuntimeError('proof checks require Python without -O')

TARGETS = set('win_SetColorNum win_SetColorFromObj win_SetColorFromObjNum win_DrawButtonBorder win_RectFill win_RectFillOutline win_DrawObjectI win_DrawObject win_DrawWindow f_23E6_0392 f_23E6_066C win_DrawElevator f_23E6_06F1 f_23E6_07A2 PrevListLine win_ProcSliderEvent f_23E6_0A53 f_22BF_094F f_22BF_0555 win_ObjAddr f_2505_033C f_2505_0006 win_WinAddr win_WinRectAddr RepointObjects win_LoadWindow win_LockWin win_LockWinHigh win_UnlockWin'.split()) | set(r.PALETTE_CALL_NAMES)
DATA = set('win_colors fd_50F6_46E2 colorEntry win_handles g_9230 win_numOfColors fd_50F6_47D6'.split())
REVIEWED = ['src/root/m20E8.c','src/root/m21FA.c','src/root/m22BF.c','src/root/m23E6.c','src/root/m2505.c','src/root/m23AE.c','src/root/m218D.c','src/root/m259D.c','src/S26/m39C7.c','src/root/m171C.c','src/root/m1A53.c','src/root/m1E57.c','src/root/m1D8E.c','src/root/m1FD2.c','src/S09/m35F5.c']
SELECTED_FACTS = ROOT/'evidence/canonical/shipped-resource-domain/facts.json'
REVIEWED = sorted(set(REVIEWED) | set(json.loads(SELECTED_FACTS.read_text())['source_sha256']))
sha = lambda data: hashlib.sha256(data).hexdigest()

class Reject(RuntimeError): pass

ASSET_PINS={'HCEGANT.NDX':'077d8aecdad5e816f0828204f7ca500a68b3a4a3288740ac75e73e44eaa8efc4','HCEGANT.DAT':'9c98c0f110e901a2c2db65944e4ebdf6b26392181e9415a34eb7b29617eaa899','SHARED.NDX':'e172f030c11f417af4b5be34dacbda9a63f157820827b40d62c08ca2c6ea7477','SHARED.DAT':'aa0d2342510f99abf57a685ea93178d9dd8d2d5be1e65b556c9b27f974012750','SOUND.NDX':'4b73be9e633b612946aac043f930b620df2483676be54c27acc08b699a84ac80','SOUND.DAT':'6a884b946d842bbddb4100a644a7aee6b3d8a9c9832aa65c0989ae50510d6629'}
def check_inputs(overrides=None):
    overrides=overrides or {}
    checks={'assets/'+p:h for p,h in ASSET_PINS.items()}
    checks['assets/SIMANT.EXE']=exe.EXPECTED_SHA256
    for rel,expected in checks.items():
        if sha(overrides.get(rel,(ROOT/rel).read_bytes()))!=expected: raise Reject('oracle/resource input changed: '+rel)
    return checks

def normalized(text):
    return ' '.join(t.text for t in csrc.tokenize(text) if t.kind not in {'ws','nl','cmt'})

def alias_map(program_aliases=None):
    table=json.loads((ROOT/'layout/symbols.json').read_text()); symbols=table['code']|table['data']
    result={n:n for n in TARGETS|DATA}
    for spelling in symbols:
        target=spelling; seen=set()
        while 'alias_of' in symbols.get(target,{}):
            if target in seen: raise Reject('cyclic symbol alias')
            seen.add(target); target=symbols[target]['alias_of']
        if target in TARGETS|DATA: result[spelling]=target
    rows = (json.loads((ROOT/'src/program.json').read_text())['aliases']
            if program_aliases is None else program_aliases)
    while True:
        before = dict(result)
        for row in rows:
            # Strip exactly the linker decoration, preserving C leading '_'.
            source, target = row['alias'][1:], row['target'][1:]
            if target in result:
                result[source] = result[target]
        if result == before:
            return result


def program_alias_subset(aliases):
    return [{k: row[k] for k in ('alias', 'target', 'offset', 'kind')}
            for row in json.loads((ROOT/'src/program.json').read_text())['aliases']
            if row['alias'][1:] in aliases or row['target'][1:] in aliases]

def inventory():
    program = json.loads((ROOT/'src/program.json').read_text())
    sources = {}
    for mod in program['modules']:
        rel = mod['source'].replace('\\','/')
        if rel in sources: raise Reject('duplicate source')
        data = (ROOT/rel).read_bytes()
        if sha(data) != mod['source_sha256']: raise Reject('inventory source hash: '+rel)
        sources[rel] = data.decode('utf8')
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT/'src').rglob('*') if p.suffix.lower() in {'.c','.asm'}}
    if actual != {p for p in sources if p.endswith(('.c','.asm'))}: raise Reject('incomplete source inventory')
    return sources

def census(texts):
    aliases=alias_map()
    calls = {n: [] for n in sorted(TARGETS)}
    declarations = {n: [] for n in sorted(TARGETS)}
    data = {n: [] for n in sorted(DATA)}
    for rel, text in sorted(texts.items()):
        if rel=='src/state/window-palette.c':
            if normalized(text)!=normalized('char far win_colors[16][6];'): raise Reject('palette owner must be the reviewed data-only declaration')
            continue
        if rel=='src/state/window-handles.c':
            if normalized(text)!=normalized('char far * far * near win_handles[34];'): raise Reject('handle owner must be the reviewed data-only declaration')
            continue
        if rel.endswith('.asm'):
            for line in text.splitlines():
                code = re.sub(r'"[^\"]*"', '', line.split(';')[0])
                for spelling in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', code):
                    if spelling.lstrip('_').casefold() in {n.casefold() for n in aliases}: raise Reject('unreviewed ASM reference: '+rel)
            continue
        toks = list(csrc.tokenize(text))
        names = {t.text for t in toks if t.kind == 'id'}
        if not names & aliases.keys(): continue
        fns = csrc.Source(text).functions()
        positions = {}
        for fn in fns:
            for node in csrc.walk(fn.body):
                if isinstance(node,csrc.Call) and isinstance(node.f,csrc.Id) and aliases.get(node.f.name) in TARGETS:
                    args = [normalized(text[a.s:a.e]) for a in node.args]
                    positions[node.f.s] = (fn.name,args)
        for t in toks:
            if t.kind == 'pp' and any(re.search(r'\b'+n+r'\b', t.text) for n in aliases): raise Reject('preprocessor escape')
            if t.kind != 'id': continue
            n=aliases.get(t.text)
            if n in DATA:
                data[n].append([rel,normalized(text[text.rfind('\n',0,t.s)+1:text.find('\n',t.e) if '\n' in text[t.e:] else len(text)])])
            if n not in TARGETS: continue
            if t.s in positions:
                caller,args = positions[t.s]
                calls[n].append([rel,caller,args,t.text]); continue
            if any(fn.name==t.text and fn.head_s<=t.s<fn.params_e for fn in fns):
                declarations[n].append([rel,'definition']); continue
            line = text[text.rfind('\n',0,t.s)+1:text.find('\n',t.e) if '\n' in text[t.e:] else len(text)]
            if re.fullmatch(r'\s*(?:extern\s+)?[^;{}]*\b'+t.text+r'\s*\([^;{}]*\)\s*;\s*',line):
                declarations[n].append([rel,'prototype']); continue
            raise Reject('non-direct/address-taken reference: '+n+' in '+rel)
    return dict(calls=calls,declarations=declarations,data=data,aliases=aliases,
                program_aliases=program_alias_subset(aliases))

def machine(name):
    image = exe.load()
    return b.Machine(SimpleNamespace(function=functions.get(name), vectors={exe.MANAGER_SEG*16+v.offset:v for v in image.vectors}, identity={'oracle_sha256':image.sha256}))

def resources():
    check_inputs()
    rows = r.decoder().parse_records('HCEGANT')[1]
    control = next(x['payload'] for x in rows if (x['id'],x['kind'])==(128,0))
    palette = next(x['payload'] for x in rows if (x['id'],x['kind'])==(129,0))
    if len(control)!=20 or struct.unpack_from('<3h',control) != (34,16,6) or len(palette)!=96: raise Reject('control/palette resource premise changed')
    windows = [(x['id'],x['payload'],r.window_domain(x['payload'])) for x in rows if x['kind']==0 and 0<=x['id']<34]
    candidates=[['HCEGANT',x['id']] for x in rows if x['kind']==0 and 0<=x['id']<=40]
    for stem in ('SHARED','SOUND'):
        candidates.extend([stem,x['id']] for x in r.decoder().parse_records(stem)[1] if x['kind']==0 and 0<=x['id']<=40)
    if sorted(candidates)!=[['HCEGANT',i] for i in range(34)]: raise Reject('successful default window lookup no longer selects only reviewed shipped windows')
    if {i for i,_,_ in windows} != set(range(34)): raise Reject('incomplete shipped windows')
    anomalies=[]; links=[]; total=0
    for wid,raw,window in windows:
        for obj in window['objects']:
            total+=1
            if obj['normal_color']>=16: raise Reject('normal color out of range')
            if obj['selected_color']>=16: anomalies.append([wid,obj['index'],obj['type'],obj['flags'],obj['normal_color'],obj['selected_color']])
            if obj['type']==8:
                link=struct.unpack_from('<h',raw,obj['offset']+40)[0]
                if link>0: links.append([wid,obj['index'],link])
            if obj['type'] in {4,7,8} and obj['selected_color']>=16: raise Reject('list/slider out of range')
    if anomalies != [[18,3,1,0xa003,0,63]] or links != [[22,8,0x1609]]: raise Reject('exception/link premise changed')
    return windows,palette,dict(windows=34,objects=total,palette_rows=16,row_bytes=6,anomalies=anomalies,slider_links=links,default_databases_kind0_ids_0_to_40=candidates)

def oracle_controls(windows,palette):
    # Actual RepointObjects -> actual checked win_ObjAddr -> actual color setter.
    # Only successful locked resource lookup and graphics sink are modeled.
    m=machine('RepointObjects'); base=b.symbol_address('win_colors')
    sink=b.symbol('f_277D_000B')
    color_pointer=0x55b30+0x8cee # original 21FA:0162/0165 stores
    noop=lambda m,a: None
    lookup=b.Callback(1,lambda m,a:(0,0xa300))
    callbacks={'f_2505_0006':lookup,'win_IsWinLocked':b.Callback(0,lambda m,a:1,('ax',)), 'f_277D_000B':b.Callback(3,noop), 'f_1CE2_0278':b.Callback(5,noop),'f_1CE2_09E2':b.Callback(6,noop),'f_1CE2_044D':b.Callback(3,noop)}
    count=0; border=0
    for wid,raw,domain in windows:
        m.run(b.Case('repoint-'+str(wid),registers={'ax':wid<<8},writes=[(0xa3000,raw),(base,palette),(b.symbol_address('g_9128'),b.words(sink['off'],sink['seg']))],callbacks={'f_2505_0006':lookup},return_kind='void'),original_entry=functions.get('RepointObjects'))
        for obj in domain['objects']:
            result=m.run(b.Case('lookup',registers={'ax':wid<<8|obj['index']},callbacks=callbacks,return_kind='farptr'),preserve=True,original_entry=functions.get('win_ObjAddr'))
            if result['return'] != 0xa3000000|obj['offset']: raise Reject('original object pointer differs')
            for selected in (0,1):
                if selected and (wid,obj['index'])==(18,3): continue
                expected=obj['selected_color'] if selected else obj['normal_color']
                for mode in (0,1):
                    m.write(0xa3000+obj['offset']+36,b.words(obj['flags']&~4|selected*4))
                    m.write(b.symbol_address('g_5A97'),bytes([mode]))
                    result=m.run(b.Case('color-object',args=[obj['offset'],0xa300],callbacks=callbacks,return_kind='void',callee_pop=4),preserve=True,original_entry=functions.get('win_SetColorFromObj'))
                    off,seg=struct.unpack('<HH',m.read(color_pointer,4))
                    if seg*16+off != base+expected*6: raise Reject('object palette pointer differs')
                    actual=[t['args'] for t in result['trace'] if t['name']=='f_277D_000B']
                    fore=palette[expected*6]*257; back=palette[expected*6+(3 if mode else 2)]*257
                    if actual != [[fore,back,fore]]: raise Reject('original palette sink values differ')
                    count+=1
                    if obj['type'] in {5,17}:
                        result=m.run(b.Case('border-object',args=[obj['offset'],0xa300],callbacks=callbacks,return_kind='void',callee_pop=4),preserve=True,original_entry=functions.get('win_DrawButtonBorder'))
                        entry=palette[obj['normal_color']*6:obj['normal_color']*6+6]
                        trace=result['trace']
                        if not selected:
                            light=[t['args'][-2:] for t in trace if t['name']=='f_1CE2_09E2']
                            dark=[t['args'][-1] for t in trace if t['name']=='f_1CE2_0278']
                            if light != [[entry[2]*257,entry[3]*257]]*3 or dark != [entry[3]*257]*3: raise Reject('normal button color arguments differ')
                        else:
                            sinkcalls=[t['args'] for t in trace if t['name']=='f_277D_000B']
                            expected_calls=[[entry[0]*257]*3]+([[entry[3]*257,entry[3]*257,entry[1]*257]] if not mode else [])
                            if sinkcalls!=expected_calls: raise Reject('selected button color arguments differ')
                        border+=1
    # Setting the actual anomalous selected bit must read the genuine row 63.
    raw=next(raw for wid,raw,_ in windows if wid==18)
    obj=r.window_domain(raw)['objects'][3]
    m.write(0xa3000,raw); m.write(0xa3000+obj['offset']+36,b.words(obj['flags']|4))
    m.run(b.Case('selected63-negative',args=[obj['offset'],0xa300],callbacks=callbacks,return_kind='void',callee_pop=4),preserve=True,original_entry=functions.get('win_SetColorFromObj'))
    off,seg=struct.unpack('<HH',m.read(color_pointer,4))
    if seg*16+off != base+378: raise Reject('selected63 contrast did not expose out-of-bounds original pointer')
    for row in range(17):
        m.run(b.Case('numeric-row',registers={'ax':row},callbacks=callbacks,return_kind='void'),preserve=True,original_entry=functions.get('win_SetColorNum'))
        off,seg=struct.unpack('<HH',m.read(color_pointer,4))
        if seg*16+off!=base+row*6: raise Reject('original numeric setter row stride changed')
    return dict(original_checked_objects=sum(len(d['objects']) for _,_,d in windows),original_setter_cases=count,original_border_cases=border,selected63_contrast_pointer_offset=378,numeric_valid_rows_checked=list(range(16)),numeric16_contrast_pointer_offset=96,models=['successful locked window resource lookup','graphics sink calls'],scope='Bounded original instruction corroboration; no full DOSBox-X runtime acceptance')

def save_load_ranges():
    m=machine('RepointObjects'); raw=m.read(b.symbol_address('fd_4E4B_0000'),308*8)
    protected={'palette':(b.symbol_address('win_colors'),96),'palette pointer':(0x55b30+0x8cee,4),'window master handles':(b.symbol_address('win_handles'),45*4),'cached window pointers':(0x55b30+0x8cf2,45*4)}
    for i in range(307):
        size,count,off,seg=struct.unpack_from('<HHHH',raw,i*8); start=seg*16+off; end=start+size*count
        if not size or not count or off+size*count>65536: raise Reject('invalid save descriptor')
        if any(start<at+width and at<end for at,width in protected.values()): raise Reject('save destination overlaps palette/window pointer state')
    if raw[-8:]!=bytes(8): raise Reject('save sentinel changed')
    return dict(original_descriptors=307,protected_ranges_intersected=0,protected={n:dict(linear=at,bytes=width) for n,(at,width) in protected.items()},scope='Successful valid-state saves; all descriptors point into static image, not heap object blocks')

def baseline(texts):
    return dict(source_pin_format='sha256-of-canonical-file-bytes',source_sha256={p:sha(texts[p].encode()) for p in REVIEWED},census=census(texts))

def validate_sources(texts,pins):
    if baseline(texts)!=pins: raise Reject('reviewed caller/writer/pointer source closure differs')

def negative_controls(texts,pins):
    edits={'direct_foreign_pointer':'void far bad(void) { win_SetColorFromObj((char far *)0); }',
        'address_taken_setter':'void (far *escape)(char far *) = win_SetColorFromObj;',
        'color_writer':'void far bad(int n) { win_colors[n][0] = 0; }',
        'raw_window_pointer':'void far bad(void) { f_2505_0006(0); }',
        'legacy_alias_setter':'void far bad(void) { f_21FA_0144((char far *)0); }',
        'legacy_alias_address_taken':'void (far *escape)(char far *) = f_21FA_0144;',
        'legacy_data_writer':'void far bad(int n) { fd_50F6_46E2[n] = 0; }',
        'mangled_asm_reference':'extrn _win_DrawButtonBorder:far',
        'uppercase_asm_reference':'EXTRN _WIN_SETCOLORFROMOBJ:FAR'}
    result=[]
    for name,edit in edits.items():
        changed=dict(texts); changed['src/'+name+('.asm' if name in {'mangled_asm_reference', 'uppercase_asm_reference'} else '.c')]=edit
        try: validate_sources(changed,pins)
        except Reject: result.append(name)
        else: raise Reject('negative source control accepted: '+name)
    changed=dict(texts); changed['src/root/m22BF.c']=changed['src/root/m22BF.c'].replace('[0x26] = color','[0x27] = color')
    try: validate_sources(changed,pins)
    except Reject: result.append('selected_field_writer')
    else: raise Reject('selected writer accepted')
    changed=dict(texts); changed['src/state/window-palette.c']='char far win_colors[16][6]; void far rogue(void) { win_colors[0][0]=1; }'
    try: validate_sources(changed,pins)
    except Reject: result.append('rogue_state_owner_function')
    else: raise Reject('rogue palette state owner accepted')
    for rel in check_inputs():
        try: check_inputs({rel:b'input-mutation-negative-control'})
        except Reject: result.append('input_mutation:'+rel)
        else: raise Reject('input mutation accepted')
    return result

def collect():
    texts=inventory(); reviewed=Path(__file__).with_name('palette-source-review.json')
    pins=json.loads(reviewed.read_text()); validate_sources(texts,pins)
    windows,palette,domain=resources()
    dynamic=oracle_controls(windows,palette)
    result=dict(status='PASS',schema='simant-window-palette-domain-v1',oracle_sha256=exe.load().sha256,inputs=check_inputs(),resource_domain=domain,source_review_sha256=sha(reviewed.read_bytes()),source_inventory_count=len(texts),original_controls=dynamic,save_load=save_load_ranges(),negative_controls=negative_controls(texts,pins))
    validate_sources(inventory(),pins)
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); args=ap.parse_args()
    import modctx
    out=modctx.under_build(ROOT/args.out); out.mkdir(parents=True,exist_ok=False)
    result=collect()
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
