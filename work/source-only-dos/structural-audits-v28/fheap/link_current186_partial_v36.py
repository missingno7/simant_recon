#!/usr/bin/env python3
"""Research-only source-only RTLink partial link; never executed."""
import json, sys, hashlib, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent/'current186-partial'
sys.path.insert(0,str(ROOT/'tools'))
import compiler, rtlink
report=json.loads((ROOT/'build/source-only-dos/build-report.json').read_text())
OUT.mkdir(exist_ok=True)
for row in report['translation_units']:
    src=ROOT/row['object']['path']; dst=OUT/(row['basename']+'.OBJ')
    blob=src.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=row['object']['sha256']:
        raise SystemExit('object pin mismatch: '+row['module'])
    shutil.copyfile(src,dst)
lines=['OUTPUT SOURCE','MAP = SOURCE S,N,A,L,V,X','NODEFLIB','LIBRARY LLIBCR, LIBH','RELOAD FAR 400','VERBOSE']
def emit(rows,prefix='FILE '):
    names=[x['basename'] for x in rows]
    for i in range(0,len(names),8): lines.append(prefix+', '.join(names[i:i+8]))
emit([r for r in report['translation_units'] if r['unit']=='root'])
emit([r for r in report['translation_units'] if r['module'].startswith('data:')])
for lo,hi in ((0,3),(4,11),(12,19),(20,26)):
    lines.append('BEGINAREA')
    for sec in range(lo,hi+1):
        rows=[r for r in report['translation_units'] if r['unit']==f'S{sec:02d}']
        lines.append('SECTION FILE '+', '.join(r['basename'] for r in rows)+(' PRELOAD' if sec==0 else ''))
    lines.append('ENDAREA')
from dos_source_bindings import rtlink_alias_delta
for a in report.get('symbolic_aliases',[]):
    quote=lambda n:'"'+n+'"' if n.startswith('@') else n
    lines.append(f"DEFINE {quote(a['alias'])} = {quote(a['owner'])}{rtlink_alias_delta(a.get('offset',0))}")
(OUT/'T.LNK').write_bytes(('\r\n'.join(lines)+'\r\n').encode('ascii'))
(OUT/'NUL.TXT').write_bytes(b'')
results=[]
for profile in ('rtlink400','rtlink610'):
    case=OUT/profile; case.mkdir(exist_ok=True)
    # Each profile needs a fresh copy because RTLink writes output/map/log in its cwd.
    for f in OUT.glob('*.OBJ'): shutil.copyfile(f,case/f.name)
    (case/'T.LNK').write_bytes((OUT/'T.LNK').read_bytes())
    rc=rtlink.run_link(case,profile=profile,timeout=900)
    logp=case/'LINK.LOG'; mapp=case/'SOURCE.MAP'
    log=logp.read_text(encoding='latin1',errors='replace') if logp.exists() else ''
    mp=mapp.read_text(encoding='latin1',errors='replace') if mapp.exists() else ''
    import re
    members=re.findall(r'LLIBCR\.LIB\(([^)]+)\)',log,re.I)
    result={'profile':profile,'return_code':rc,'has_map':bool(mp),'has_exe':(case/'SOURCE.EXE').exists(),
            'diagnostic_excerpt':log[-12000:],'selected_member_count':len(members),
            'selected_fheap_members':[x for x in members if x.lower() in ('malloc.asm','free.asm','fmalloc.asm','frealloc.asm','fdata.asm','dos\\stdalloc.asm','dos\\stdenvp.asm','dos\\stdargv.asm','dos\\crt0.asm')],
            'selected_all_member_names':members,
            'map_has_fheap_symbol':bool(re.search(r'^\s*[0-9A-Fa-f]+:[0-9A-Fa-f]+\s+(?:Res\s+)?__fheap(?:\s|$)',mp,re.M)),
            'exe_executed':False}
    results.append(result)
    print(profile,'rc=',rc,'map=',bool(mp),'exe=',result['has_exe'],'selected=',len(members),'fheap_chain=',result['selected_fheap_members'])
(OUT/'current186-partial-link-v36.json').write_text(json.dumps({'status':'RESEARCH_PARTIAL_LINK_NEVER_EXECUTED','current_object_count':len(report['translation_units']),'object_pins_verified':True,'aliases_emitted':len(report.get('symbolic_aliases',[])),'runs':results},indent=2)+'\n')
