"""Build SDL3 from the sole current canonical program inventory.

All ordinary owners originate in canonical C/ASM; platform files provide native
representations and services. Open historical/native contracts are listed in
the platform manifest and do not acquire an acceptance claim by compiling.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from canonical_native_abi import scalar, tokenizer as csrc, integer_frontend, register_returns, semantic_spans
from canonical_native_abi.source_views import (
    GRAPHICS_SCALARS,
    audio_overlap_views,
    callback_views,
    canonical_interior_views,
    centralize,
    edit_cache_view,
    graphics_canonical_views,
    menu_resource_view,
    screen_clip_canonical_views,
    translate_29d6_port_block,
    unused_cache_release_argument,
)
from canonical_native_abi.lexical import rename
from canonical_native_abi import rng
from canonical_native_abi import audio
from canonical_native_abi import audio_shared_state_preword
from canonical_native_abi import fonts
from canonical_native_abi import pointer_globals
from canonical_native_abi import varargs
from canonical_native_abi import windows
from canonical_native_abi import window_loader
from canonical_native_abi import timer
from canonical_native_abi import startup_bundle
from canonical_native_abi import main_preflight
from canonical_native_abi import findindex_native_guard
from canonical_native_abi import crt_abi
from canonical_native_abi import spider_inline_source
from canonical_native_abi import m1b73_queue_source
from canonical_native_abi import m1b73_event_source
from canonical_native_abi import event_word_switch
from canonical_native_abi import file_select_host
from canonical_native_abi import menu_s17_preword
from canonical_native_abi import list_text_handle
from canonical_native_abi import clip_stack_native
from canonical_native_abi import cache_table_native
from canonical_native_abi import countdown_host
from canonical_native_abi import window_parameters
from canonical_native_abi import newgame_zoom_window_v1
from canonical_native_abi import s26_window_object_views_v1
from canonical_native_abi import load_string_ant
from canonical_native_abi import cross_tu_pointer_widths
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'tools'))
from workspace import prepare_output, retire
ROOT=PROJECT
OUT=None
SDK=None
CC=None
PLATFORM=json.loads((Path(__file__).parent/'platform.json').read_text())
ABI_MODULES={'rng':rng,'audio':audio,'audio_shared_state_preword':audio_shared_state_preword,'fonts':fonts,'pointer_globals':pointer_globals,'varargs':varargs,'windows':windows,'window_loader':window_loader,'timer':timer,'startup_bundle':startup_bundle,'main_preflight':main_preflight,'findindex_native_guard':findindex_native_guard,'crt_abi':crt_abi,'spider_inline_source':spider_inline_source,'m1b73_queue_source':m1b73_queue_source,'m1b73_event_source':m1b73_event_source,'event_word_switch':event_word_switch,'file_select_host':file_select_host,'menu_s17_preword':menu_s17_preword,'list_text_handle':list_text_handle,'clip_stack_native':clip_stack_native,'cache_table_native':cache_table_native,'countdown_host':countdown_host,'window_parameters':window_parameters,'newgame_zoom_window_v1':newgame_zoom_window_v1,'s26_window_object_views_v1':s26_window_object_views_v1,'load_string_ant':load_string_ant}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

LTO_BASELINE=PROJECT/'portable/canonical_native_abi/lto-type-mismatch-baseline.json'
LTO_DIAGNOSTIC=re.compile(
    r"^(?P<path>.*?):\d+:\d+: (?:warning|error): (?P<message>.*) "
    r"\[-W(?:error=)?(?:lto-type-mismatch|odr)\]$")
LTO_NOTE=re.compile(r'^(.*?):\d+:\d+: note: (?P<message>.*)$')
LTO_SYMBOL=re.compile(r"type of ['\u2018](.*?)['\u2019] does not match original declaration")

def lto_mismatch_signatures(text):
    found=[];active=None
    for line in text.splitlines():
        diagnostic=LTO_DIAGNOSTIC.match(line)
        if diagnostic:
            if active:found.append(active)
            symbol=LTO_SYMBOL.search(diagnostic.group('message'))
            active=({'symbol':symbol.group(1),'at':Path(diagnostic.group('path')).name,
                     'previous':'','details':[]} if symbol else None)
            continue
        if not active:continue
        note=LTO_NOTE.match(line)
        if not note:continue
        message=note.group('message').strip()
        if message.endswith('was previously declared here'):
            active['previous']=Path(note.group(1)).name
        elif message and not message.startswith('code may be misoptimized') and message not in active['details']:
            active['details'].append(message)
    if active:found.append(active)
    return sorted({json.dumps(item,sort_keys=True,separators=(',',':')) for item in found})

def check_lto_declarations(text):
    observed=set(lto_mismatch_signatures(text))
    baseline=set(json.loads(LTO_BASELINE.read_text(encoding='utf-8')))
    unexpected=sorted(observed-baseline)
    return {'passed':not unexpected,'observed_mismatches':len(observed),
            'known_mismatches':len(observed&baseline),
            'unexpected':[json.loads(item) for item in unexpected],
            'baseline':str(LTO_BASELINE)}

def main():
    global ROOT, OUT, SDK, CC
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=PROJECT/'build/current/portable')
    parser.add_argument('--sdk',type=Path,default=PROJECT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32')
    parser.add_argument('--cc',default='C:/msys64/mingw64/bin/gcc.exe')
    parser.add_argument('--jobs',type=int,default=6)
    args=parser.parse_args();ROOT=PROJECT;OUT=args.out.absolute();SDK=args.sdk.resolve();CC=args.cc
    prepare_output(OUT, PROJECT/'build/current/portable')
    copyroot=PROJECT
    canonical=json.loads((ROOT/'src/program.json').read_text())
    mismatched=[u['source'] for u in canonical['modules'] if sha(ROOT/u['source'])!=u['source_sha256']]
    if mismatched:raise ValueError('active canonical program/source inventory differs: '+str(mismatched))
    for dependency in PLATFORM.get('third_party_dependencies', []):
        provenance=ROOT/dependency['provenance']
        pins=json.loads(provenance.read_text())['sha256']
        for name,expected in pins.items():
            if sha(provenance.parent/name)!=expected:
                raise ValueError('third-party source differs from provenance: '+name)
    def current_inputs():
        paths={ROOT/'src/program.json',PROJECT/'portable/platform.json',PROJECT/'portable/semantic-spans.json',Path(__file__),register_returns.CONTRACT_PATH,
               integer_frontend.WORD_CONTRACT_PATH}
        paths.update(ROOT/u['source'] for u in canonical['modules'])
        paths.update(PROJECT/rel for rel in PLATFORM['services']+PLATFORM['headers'])
        paths.update((PROJECT/'portable/canonical_native_abi').glob('*.py'))
        paths.update((PROJECT/'portable/canonical_native_abi/integer_fake_libc').rglob('*.h'))
        paths.add(PROJECT/'portable/tests/integer_semantics/requirements.txt')
        paths.add(LTO_BASELINE)
        paths.update(Path(integer_frontend.pycparser.__file__).parent.glob('*.py'))
        paths.add(PROJECT/'portable/whole_program/application.c')
        paths.update((PROJECT/'portable/runtime/bios-reference').rglob('*'))
        paths.update(ROOT/'assets'/name for name in PLATFORM['runtime_assets'])
        paths.update(ROOT/rel for rel in ['tools/compiler.py','tools/omf.py','tools/workspace.py','layout/toolchain.json','layout/manifest.json'])
        for dependency in PLATFORM.get('third_party_dependencies', []):
            paths.update(ROOT/dependency[k] for k in ('license','provenance'))
        return {p.relative_to(PROJECT).as_posix():sha(p) for p in sorted(paths) if p.is_file()}
    input_pins=current_inputs()
    revision=subprocess.check_output(['git','-c','safe.directory='+PROJECT.as_posix(),
        'rev-parse','HEAD'],cwd=PROJECT,text=True).strip()
    build_identity={'source_revision':revision,
        'build_inputs_sha256':hashlib.sha256(json.dumps(input_pins,sort_keys=True).encode()).hexdigest()}
    inventory={'translation_units':[dict(module=u['key'],source=u['source'],canonical_destination=u['source'],lang=u['lang']) for u in canonical['modules']]}
    aliases=[dict(alias=x['alias'],owner=x.get('target',x.get('owner')),offset=x.get('offset',0),kind=x['kind']) for x in canonical['aliases']]
    # One canonical program inventory and whole canonical source files.
    function_aliases={x['alias'].lstrip('_@'):x['owner'].lstrip('_@') for x in aliases if x['kind']=='code'}
    thunk_text=(ROOT/'src/root/m2CFB.asm').read_text(encoding='latin1')
    function_aliases.update({a.lstrip('_@'):b.lstrip('_@') for a,b in re.findall(r'(?m)^\s*(\w+):\s+jmp\s+(\w+)\s*$',thunk_text)})
    for alias,target in list(function_aliases.items()):
        seen=set()
        while target in function_aliases and target not in seen:
            seen.add(target);target=function_aliases[target]
        function_aliases[alias]=target
    object_identities={x['alias'].lstrip('_@'):x['owner'].lstrip('_@') for x in aliases
                       if x['kind']!='code' and not x.get('offset',0) and x['owner'].lstrip('_@')!='driver_callback_table'}
    alias_specs={x['alias'].lstrip('_@'):x for x in aliases if x['kind']!='code'}
    callback_slots={n:x['offset']//4 for n,x in alias_specs.items() if x['owner'].lstrip('_@')=='driver_callback_table'}
    abis=ABI_MODULES;rows=[];errors=[]
    native_scalar_names={name for counts in abis['audio_shared_state_preword']._SHARED_EXTERN_COUNTS.values() for name in counts}
    source_texts={u['canonical_destination']:(ROOT/u['source']).read_text(encoding='latin1')
                  for u in inventory['translation_units'] if u['lang']=='c'}
    native_source_texts,cross_tu_pointer_receipt=cross_tu_pointer_widths.adapt(source_texts,object_identities)
    spans=semantic_spans.Contracts(ROOT,source_texts)
    event_definition=re.search(r'struct Event\s*\{[^{}]*\};',source_texts['src/root/m1FD2.c'],re.S).group(0)
    queue_header=OUT/'include/portable/whole_program/types/input_queue.h'
    queue_header.parent.mkdir(parents=True,exist_ok=True)
    queue_header.write_text('#ifndef SIMANT_CANONICAL_INPUT_QUEUE_NATIVE_ABI_H\n#define SIMANT_CANONICAL_INPUT_QUEUE_NATIVE_ABI_H\n#include "portable/whole_program/types/timer.h"\n'+scalar.convert(event_definition)+'\n#pragma pack(push,2)\nstruct InputQueueDescriptor { struct Rect r; void (*fn)(void); uint16_t callback_segment_word; struct Event *records; char a,b,c,d; };\n#pragma pack(pop)\nextern struct InputQueueDescriptor g_5FF2;\nextern struct Event input_queue[7];\n#endif\n')
    scalar_header=OUT/'dos_types.h';scalar_header.write_text('#include <stdint.h>\n#include <stddef.h>\nuint8_t dos_keyboard_modifiers(void);\nvoid *dos_malloc(uint16_t);\nvoid dos_free(void *);\nvoid *dos_realloc(void *,uint16_t);\nstruct Event; struct Point; struct Rect;\n')
    (OUT/'canonical_data_views.h').write_text('#ifndef SIMANT_CANONICAL_DATA_VIEWS_H\n#define SIMANT_CANONICAL_DATA_VIEWS_H\n#include <stdint.h>\nunion CanonicalWordBytes14 { uint8_t bytes[14]; int16_t words[7]; };\nunion CanonicalWordBytes4 { uint8_t bytes[4]; int16_t words[2]; };\nextern union CanonicalWordBytes14 fd_3D57_07CC;\nextern union CanonicalWordBytes4 fd_3D57_0C1A;\nextern void *fd_3D57_082A[20];\nextern char *fd_55B3_1CD4[5];\n#endif\n')
    (OUT/'canonical_graphics_data.h').write_text('#ifndef SIMANT_CANONICAL_GRAPHICS_DATA_H\n#define SIMANT_CANONICAL_GRAPHICS_DATA_H\n#include <stdint.h>\ntypedef struct CanonicalAsmPoint { int16_t x,y; } CanonicalAsmPoint;\nextern CanonicalAsmPoint g_3DA0;\n'+'\n'.join('extern int16_t '+n+';' for n in GRAPHICS_SCALARS)+'\nextern uint8_t g_41C0[16];\nextern char g_3D20[128];\n#endif\n')
    (OUT/'canonical_edit_cache.h').write_text('#ifndef SIMANT_CANONICAL_EDIT_CACHE_H\n#define SIMANT_CANONICAL_EDIT_CACHE_H\n#include <stdint.h>\nunion CanonicalEditCache { int16_t rows[30][40]; int16_t linear[1200]; };\nextern union CanonicalEditCache fd_50F6_15C4;\n#endif\n')
    native_startups={}
    try:
        native_startups,_=abis['startup_bundle'].convert_startup_sources(source_texts['src/root/m15F8.c'],source_texts['src/S15/m384C.c'])
    except Exception as exc:errors.append({'source':'startup pair','stage':'ABI conversion','error':str(exc)})
    def apply(name,function,text,*args,**kwargs):
        try:
            value=getattr(abis[name],function)(*args,**kwargs)
            return value[0] if isinstance(value,tuple) else value.text if hasattr(value,'text') else value
        except Exception as exc:
            errors.append({'source':rel,'stage':name+'.'+function,'error':str(exc)})
            return text
    for unit in inventory['translation_units']:
        rel=unit['canonical_destination'];row={'source':rel,'module':unit['module'],'lang':unit['lang']}
        if unit['lang']=='asm':
            row['status']='NEEDS_SYMBOLIC_ASM_TRANSLATION_OR_PLATFORM_REPLACEMENT';rows.append(row);continue
        original=source_texts[rel];text=native_source_texts[rel]
        if rel in native_startups:text=native_startups[rel]
        if rel=='src/root/m0093.c':text=apply('rng','adapt',text,text)
        if rel=='src/root/m0250.c':
            result=apply('spider_inline_source','adapt',text,text.encode('latin1'),rel)
            text=result.decode('latin1') if isinstance(result,bytes) else result
        if rel=='src/root/m1FD2.c':
            text=apply('timer','adapt',text,text)
            text=apply('m1b73_queue_source','adapt',text,text,rel)
            text=re.sub(r'struct Event\s*\{[^{}]*\};','',text,count=1,flags=re.S)
            initializer=r'struct Timer g_5FF2\s*=\s*\{\s*\{\s*0,\s*0,\s*0,\s*0xff\s*\},\s*0,\s*\(int\)\(struct Event\s+near\s*\*\)input_queue,\s*5,\s*0,\s*10,\s*0\s*\};'
            text,count=re.subn(initializer,'struct InputQueueDescriptor g_5FF2 = { {0,0,0,0xff},0,0,input_queue,5,0,10,0 };',text)
            if count!=1:errors.append({'source':rel,'stage':'canonical input queue native pointer','error':'initializer shape differs'})
            text='#include "portable/whole_program/types/input_queue.h"\n'+text
        if rel in abis['audio_shared_state_preword'].SOURCE_MODULES:
            if rel.startswith('src/root/') and rel.rsplit('/',1)[1] in {'m284A.c','m29F0.c','m277E.c','m29D6.c','m293A.c','m290D.c'}:
                text=translate_29d6_port_block(text) if rel=='src/root/m29D6.c' else apply('audio','adapt',text,rel,text)
            shared=abis['audio_shared_state_preword']._SHARED_EXTERN_COUNTS.get(rel,{})
            deferred=set(shared)&native_scalar_names
            text=apply('audio_shared_state_preword','adapt',text,rel,text,original,deferred_scalar_externs=deferred)
        if rel in {'src/S10/m35F5.c','src/S19/m384C.c'}:text=apply('m1b73_event_source','adapt',text,text,rel)
        text=apply('event_word_switch','adapt',text,text,rel)
        if rel in {'src/S10/m35F5.c','src/S17/m384C.c'}:
            text=apply('menu_s17_preword','adapt_s17_source' if '/S17/' in rel else 'adapt_s10_source',text,text)
        if rel=='src/S09/m35F5.c':
            result=apply('file_select_host','adapt',text,text.encode('latin1'),rel)
            text=result.decode('latin1') if isinstance(result,bytes) else result
        if rel=='src/root/m23E6.c':text=apply('list_text_handle','adapt',text,text)
        if rel=='src/root/m1A96.c':text=apply('cache_table_native','adapt_reviewed',text,text,rel)
        if rel=='src/S26/m39C7.c':text=apply('s26_window_object_views_v1','adapt',text,text,rel)
        text=apply('clip_stack_native','adapt',text,text,rel)
        if rel in abis['crt_abi'].SUPPORTED:text=apply('crt_abi','adapt',text,text,rel)
        if rel=='src/root/m1986.c':text=apply('findindex_native_guard','adapt_whole_source',text,text,rel)
        text=apply('fonts','adapt',text,rel,text)
        text=apply('pointer_globals','adapt',text,rel,text)
        if rel.startswith('src/root/') and rel.rsplit('/',1)[1] in {'m2505.c','m20E8.c','m23AE.c','m22BF.c','m21FA.c','m218D.c'}:
            text=apply('windows','convert_window_source',text,text)
        text=apply('window_loader','adapt',text,text,rel)
        text=apply('varargs','adapt',text,text,rel)
        text=re.sub(r'\*\s*\(\s*(?:(unsigned)\s+)?char\s+far\s*\*\s*\)\s*0x0*417L',lambda m:'dos_keyboard_modifiers()',text,flags=re.I)
        text=rename(text,function_aliases)
        text=scalar.convert(text)
        if rel=='src/root/m075B.c':text=apply('load_string_ant','adapt',text,text)
        text=centralize(text)
        text=rename(text,object_identities)
        text=canonical_interior_views(text)
        text=audio_overlap_views(text,rel)
        text=graphics_canonical_views(text,rel)
        text=menu_resource_view(text,rel)
        text=screen_clip_canonical_views(text,rel)
        text=re.sub(r'(?m)^\s*extern\s+(?:PortableWholeAudioVoiceSlot\s+fd_55B3_6B4E\[33\]|int16_t\s+fd_55B3_6BA4\[128\])\s*;\s*\n','',text)
        text=edit_cache_view(text)
        text=callback_views(text,callback_slots)
        text=apply('countdown_host','adapt',text,text,rel)
        text=unused_cache_release_argument(text) if rel=='src/root/m00F8.c' else text
        text=apply('window_parameters','adapt',text,text,rel)
        if rel=='src/S15/m384C.c':text=apply('newgame_zoom_window_v1','adapt_postword',text,text,rel,original_source=original)
        # Database record bytes retain their wire sizes; only runtime index
        # pointers widen. The native type adapter is intentionally explicit.
        db_family=rel in {'src/root/m1986.c','src/root/m19A9.c','src/root/m1A28.c'}
        if db_family:
            text=re.sub(r'\btypedef\s+struct\s*\{[^{}]*\}\s*(?:IndexEntry|IndexHeader|DBHeader|DBRecordHeader|OpenDBRec)\s*;','',text,flags=re.S)
            text='#include "portable/whole_program/types/database.h"\n'+text
        if unit['module']=='source-owned:database-record-state':
            # Its canonical definition names/counts are retained verbatim;
            # the shared runtime/wire ABI supplies only the type spelling.
            ts=csrc.tokenize(text);last_typedef=max((t.e for t in ts if t.text==';'),default=0)
            owned=re.search(r'(?m)^OpenDBRec\s+fd_50F6_3958\s*\[4\]\s*;',text)
            if owned:text='#include "portable/whole_program/types/database.h"\n'+text[owned.start():]
        if unit['module']=='source-owned:database-index-state':
            owned=re.search(r'(?m)^IndexEntry\s+\*\s+fd_50F6_3952\s*;',text)
            if not owned:raise ValueError('canonical database index cursor owner differs')
            text='#include "portable/whole_program/types/database.h"\n'+text[owned.start():]
        text=spans.extract(rel,text)
        native_headers=re.findall(r'(?m)^\s*#include\s+"(portable/[^"\n]+)"\s*$',text)
        for h in native_headers:text=re.sub(r'(?m)^\s*#include\s+"'+re.escape(h)+r'"\s*\n','',text)
        prefix='#include "dos_types.h"\n#include "portable/whole_program/platform/dos_memory.h"\n#include "portable/whole_program/platform/dos_io.h"\n'
        prefix+=''.join('#include "'+h+'"\n' for h in dict.fromkeys(native_headers))
        if rel.startswith('src/S09/'):prefix+='#include "portable/whole_program/platform/dos_files.h"\n'
        if rel.startswith('src/S20/'):prefix+='#include <ctype.h>\n'
        if rel=='src/S17/m384C.c':prefix+='#include "portable/whole_program/menu_globals.h"\n'
        if rel=='src/S19/m384C.c':prefix+='extern void ProcHistoryEvent(struct Event *);\nextern void ProcYardEvent(struct Event *);\n'
        try:
            text,row['register_returns']=register_returns.adapt(text,rel)
        except ValueError as exc:
            errors.append({'source':rel,'stage':'register return ABI','error':str(exc)})
        dest=OUT/(unit['module'].replace(':','_').replace('@','_')+'.c')
        text=prefix+'#pragma pack(push,2)\n'+text+'\n#pragma pack(pop)\n'
        dest.write_text(text,encoding='latin1')
        row.update(generated=str(dest),status='WHOLE_CANONICAL_TU_CONVERTED');
        if rel=='src/root/m171C.c':
            row.update(status='PLATFORM_BOUNDARY',platform_boundary='Native malloc/free/realloc service replaces DOS segment:offset heap representation; canonical DOS heap TU is excluded from native compilation.')
        rows.append(row)
    native_rows=[{'source':rel,'generated':str(PROJECT/rel)}
                 for rel in PLATFORM['services']]
    span_source,span_receipt=spans.emit(OUT)
    span_rows=[{'source':'canonical semantic span storage','generated':str(span_source)}]
    # Assemble the current symbolic audio source only to resolve its explicit
    # OFFSET relocations. It supplies no code, capacities or original image bytes.
    sys.path.insert(0,str(ROOT/'tools'))
    import compiler
    from canonical_native_abi import asm_data
    compiler.WORK=OUT/'assembler'
    audio_source=ROOT/'src/root/m28BC.asm'
    assembled=compiler.assemble(audio_source.read_text(encoding='latin1'),'masm510')
    (OUT/'assembler.log').write_text(assembled.log)
    if not assembled.ok:raise ValueError('current canonical audio ASM did not assemble')
    object_path=OUT/'audio-offsets.obj';object_path.write_bytes(assembled.obj)
    source_path=OUT/'audio-offsets.asm';source_path.write_bytes(audio_source.read_bytes())
    asm_data.ROOT=ROOT;asm_data.WORK=OUT;asm_data.AUDIO_OBJECT=object_path;asm_data.AUDIO_SOURCE=source_path
    paths=['src/root/m1B73.asm','src/root/m1B4E.asm','src/root/m28BC.asm','src/S02/m3126.asm','src/root/m195A.asm','src/root/m2650.asm','src/root/m1FBD.asm']
    facts=[asm_data.data_facts(ROOT/p) for p in paths]
    asm_receipt={'modules':facts,'mouse':asm_data.emit_mouse(facts[0]),'queues':asm_data.emit_mouse_queues(facts[0]),'numeric':asm_data.emit_numeric(facts),'audio':asm_data.emit_audio(facts)}
    (OUT/'asm-data-facts.json').write_text(json.dumps(asm_receipt,indent=2)+'\n')
    patterns=next(r for r in asm_receipt['numeric'] if r['name']=='g_41D0')
    graphics_header=OUT/'canonical_graphics_data.h'
    text_owner=next(r for r in asm_receipt['numeric'] if r['name']=='g_5ABE')
    aliases=text_owner['alias_layout']
    pixel_count=aliases['pixels']['count']
    string_count=aliases['string']['count']
    tail_count=aliases['anonymous']['count']
    text_header=(
        'extern uint8_t g_41D0['+str(patterns['native_count'])+'];\n'
        'typedef struct CanonicalTextBitmapAliases {\n'
        '    uint8_t g_5ABE['+str(pixel_count)+'];\n'
        '    uint8_t g_5ECE['+str(string_count)+'];\n'
        '    uint8_t g_5F1D;\n'
        '    uint8_t anonymous['+str(tail_count)+'];\n'
        '} CanonicalTextBitmapAliases;\n'
        'typedef union CanonicalTextBitmapStorage {\n'
        '    CanonicalTextBitmapAliases aliases;\n'
        '    uint8_t clear_span['+str(text_owner['count'])+'];\n'
        '} CanonicalTextBitmapStorage;\n'
        'extern uint16_t g_5ABA, g_5ABC;\n'
        'extern CanonicalTextBitmapStorage g_5ABE;\n'
        'extern uint8_t g_5ECE['+str(string_count)+'];\n'
        'extern uint8_t g_5F1D;\n'
        '#define CANONICAL_TEXT_BITMAP_PIXELS (g_5ABE.aliases.g_5ABE)\n'
        '#define CANONICAL_TEXT_BITMAP_STRING (g_5ABE.aliases.g_5ECE)\n'
        '#define CANONICAL_TEXT_BITMAP_TERMINATOR (&g_5ABE.aliases.g_5F1D)\n'
        '#define CANONICAL_TEXT_BITMAP_CLEAR_SPAN (g_5ABE.clear_span)\n'
        '#define CANONICAL_TEXT_BITMAP_BITS ((char *)CANONICAL_TEXT_BITMAP_CLEAR_SPAN)\n'
    )
    graphics_header.write_text(graphics_header.read_text().replace(
        '#endif\n',text_header+'#endif\n'))
    # Source-derived ASM declarations must exist before preprocessing the
    # complete canonical C TUs. The expression pass is the final C lowering.
    for row in rows:
        if row['lang']!='c':continue
        dest=Path(row['generated'])
        try:
            text,row['integer_expressions']=integer_frontend.convert(dest.read_text(encoding='latin1'),dest.as_posix(),CC,
                [OUT/'include',PROJECT,OUT,PROJECT/'portable/whole_program'],canonical_source=row['source'])
            dest.write_text(text,encoding='latin1')
        except Exception as exc:
            errors.append({'source':row['source'],'stage':'integer frontend','error':str(exc)})
    # Modern presentation boundary (platform/window_hosting.c): cross-module
    # calls into m1E57's clip entry points are observed; bodies are canonical.
    WINDOW_HOSTING_WRAPS=['-Wl,--wrap='+name for name in PLATFORM['window_hosting_wraps']]
    asm_rows=[{'source':'canonical symbolic ASM data: '+name,'generated':str(OUT/name),
               'status':'DATA_FROM_SYMBOLIC_ASM_DIRECTIVES'} for name in PLATFORM['ASM_data_recipes']]
    def compile_row(row):
        source=Path(row['generated'])
        relative=source.relative_to(PROJECT) if source.is_relative_to(PROJECT) else Path('generated')/source.name
        obj=(OUT/'objects'/relative).with_suffix('.o');obj.parent.mkdir(parents=True,exist_ok=True)
        row['object']=str(obj)
        standard = '-std=c++17' if source.suffix == '.cpp' else '-std=c11'
        command=[CC,standard,'-flto','-ffat-lto-objects','-g','-fsigned-char','-fno-builtin','-fno-strict-aliasing',
                 '-DSIMANT_NATIVE_LITTLE_ENDIAN=1','-Werror=implicit-function-declaration','-Werror=implicit-int',
                 '-I',str(OUT/'include'),'-I',str(copyroot),'-I',str(OUT),'-I',str(copyroot/'portable/whole_program'),
                 '-I',str(SDK/'include'),'-c',str(source),'-o',str(obj)]
        if source.suffix == '.cpp':
            command=[x for x in command if not x.startswith('-Werror=implicit-')]
        if row['source']=='portable/whole_program/platform/sdl3/diagnostics.c':
            command.insert(1,'-DSIMANT_BUILD_REVISION="'+revision+'"')
        if row['source']=='src/root/m25E7.c':command.insert(1,'-Dfont_MakeImage=sim_font_make_image_source')
        run=subprocess.run(command,capture_output=True,text=True)
        obj.with_suffix('.compile.txt').write_text(run.stdout+run.stderr)
        row['compile']={'passed':run.returncode==0,'exit_code':run.returncode,'command':command,
                        'errors':re.findall(r'^.*(?:error:|fatal error:).*$',run.stderr,re.M)}
        return str(obj) if run.returncode==0 else None
    compile_rows=[r for r in rows+native_rows+asm_rows+span_rows if 'generated' in r and r.get('source')!='src/root/m171C.c']
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        objects=[obj for obj in pool.map(compile_row,compile_rows) if obj]
    link={'passed':False,'status':'SKIPPED_REQUIRED_INPUT_FAILURE'}
    declaration_check={'passed':False,'status':'SKIPPED_REQUIRED_INPUT_FAILURE'}
    app_link={'passed':False,'status':'SKIPPED_REQUIRED_INPUT_FAILURE','undefined':[]}
    stable_before_link=current_inputs()==input_pins
    required_passed=not errors and all(r['compile']['passed'] for r in compile_rows) and stable_before_link
    if required_passed:
        linked=OUT/'canonical_core.o'
        # Keep collect2's Windows command below the process argument limit.
        # GCC expands its own @files before spawning collect2; pass the remaining
        # objects directly to the linker in original order instead.
        response=OUT/'core-objects.rsp'
        response.write_text('\n'.join('"'+Path(p).as_posix()+'"' for p in objects[1:])+'\n',encoding='utf-8')
        declaration_output=OUT/'declaration-check.o'
        declaration_command=[CC,'-flto','-Wlto-type-mismatch','-Wodr','-r',objects[0],'-Wl,@core-objects.rsp','-o',str(declaration_output)]
        declaration_run=subprocess.run(declaration_command,cwd=OUT,capture_output=True,text=True)
        declaration_text=declaration_run.stdout+declaration_run.stderr
        (OUT/'declaration-check.txt').write_text(declaration_text)
        declaration_check=check_lto_declarations(declaration_text)
        declaration_check.update({'exit_code':declaration_run.returncode,'command':declaration_command})
        if declaration_run.returncode!=0:
            declaration_check['passed']=False
            declaration_check.setdefault('unexpected',[]).append('GCC LTO declaration link failed')
        command=[CC,'-Wlto-type-mismatch','-Wodr','-r',objects[0],'-Wl,@core-objects.rsp','-o',str(linked)]
        run=subprocess.run(command,cwd=OUT,capture_output=True,text=True);(OUT/'core-link.txt').write_text(run.stdout+run.stderr)
        link={'passed':run.returncode==0,'command':command,'exit_code':run.returncode,
              'working_directory':str(OUT),'object_inputs':objects,
              'response_file':str(response),'response_file_sha256':sha(response)}
        if link['passed']:
            application=PROJECT/'portable/whole_program/application.c'
            # Link original objects directly so DWARF locations survive. A
            # relocatable aggregate can invalidate the debugger's argument views.
            app_response=OUT/'application-objects.rsp'
            app_response.write_text('\n'.join('"'+Path(p).as_posix()+'"' for p in objects)+'\n',encoding='utf-8')
            # System DbgHelp cannot read MinGW DWARF; exports provide native
            # function names. Keep -g for offline source-line analysis as well.
            # -fno-lto: link the fat objects' regular code. The declaration check above
            # keeps LTO's cross-TU type audit; --wrap only applies outside LTO.
            application_command=[CC,'-fno-lto','-std=c11','-g','-fsigned-char','-fno-strict-aliasing','-I',str(OUT/'include'),'-I',str(copyroot),'-I',str(OUT),
                '-I',str(copyroot/'portable/whole_program'),'-I',str(SDK/'include'),str(application),'-Wl,@application-objects.rsp','-Wl,--wrap=exit',*WINDOW_HOSTING_WRAPS,'-Wl,--export-all-symbols','-static','-lstdc++',str(SDK/'lib/libSDL3.dll.a'),'-o',str(OUT/'simant-canonical.exe')]
            app_run=subprocess.run(application_command,cwd=OUT,capture_output=True,text=True)
            (OUT/'application-link.txt').write_text(app_run.stdout+app_run.stderr)
            app_link={'passed':app_run.returncode==0,'command':application_command,'exit_code':app_run.returncode,
                      'working_directory':str(OUT),'object_inputs':objects,
                      'response_file':str(app_response),'response_file_sha256':sha(app_response),
                      'undefined':sorted(set(re.findall(r"undefined reference to [`']([^'`]+)['`]",app_run.stderr)))}
            if app_link['passed']:
                build_identity['executable_sha256']=sha(OUT/'simant-canonical.exe')
                (OUT/'simant-build-id.txt').write_text(''.join(f'{key}={value}\n' for key,value in build_identity.items()),encoding='ascii')
                shutil.copyfile(SDK/'bin/SDL3.dll',OUT/'SDL3.dll')
                shutil.copytree(PROJECT/'portable/runtime/bios-reference',OUT/'runtime-bios-fonts')
                (OUT/'runtime-assets').mkdir()
                for name in PLATFORM['runtime_assets']:
                    shutil.copyfile(ROOT/'assets'/name,OUT/'runtime-assets'/name)
                for resource in PLATFORM['generated_runtime_resources']:
                    if resource['bytes']!=0:raise ValueError('unsupported generated platform resource')
                    (OUT/'runtime-assets'/resource['path']).write_bytes(b'')
    stable_at_end=current_inputs()==input_pins
    passed=required_passed and declaration_check['passed'] and link['passed'] and app_link['passed'] and stable_at_end
    executable=OUT/'simant-canonical.exe'
    if executable.is_file() and not passed:retire(executable)
    report={'schema':'canonical-native-complete-attempt-v1','passed':passed,'input_pins':input_pins,
        'build_identity':build_identity,
        'sdk':{'path':str(SDK),'import_library_sha256':sha(SDK/'lib/libSDL3.dll.a'),'runtime_sha256':sha(SDK/'bin/SDL3.dll')},
        'input_stability':{'before_link':stable_before_link,'at_end':stable_at_end},
        'runtime_resources':{'shipped':{name:sha(ROOT/'assets'/name) for name in PLATFORM['runtime_assets']},'generated':PLATFORM['generated_runtime_resources']},
        'executable':{'path':str(executable),'sha256':sha(executable)} if passed else None,'claim':'One canonical source program plus explicit ABI/platform services. Preview limitations are explicit; no DOS equality claim.',
        'canonical_TUs':rows,'native_services':native_rows,'canonical_ASM_data_translations':asm_rows,'semantic_spans':span_receipt,'semantic_span_storage':span_rows,'cross_tu_pointer_widths':cross_tu_pointer_receipt,'declaration_check':declaration_check,'preview_limitations':PLATFORM['preview_limitations'],'conversion_failures':errors,'core_link':link,'application_link':app_link,
        'counts':{'canonical_C_count':sum(r['lang']=='c' for r in rows),'canonical_C_compile_pass':sum(r.get('compile',{}).get('passed',False) for r in rows),
             'ASM_TUs_requiring_translation_or_platform_boundary':sum(r['lang']=='asm' for r in rows),
             'native_services':len(native_rows),'native_services_compile_pass':sum(r['compile']['passed'] for r in native_rows),
             'conversion_failures':len(errors)}}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts'],indent=2))
    print(json.dumps({'core_link':link['passed'],'application_link':app_link['passed'],'undefined_count':len(app_link['undefined'])}))
    return int(not passed)

if __name__=='__main__':raise SystemExit(main())
