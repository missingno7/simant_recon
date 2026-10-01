from pathlib import Path
import sys,json,re,itertools
sys.path.insert(0,'tools')
import modctx,csrc,variants,autosearch
out=Path('build/workers/phase_next')
def run(name,base,vs,folder):
 ctx=modctx.resolve(func=name);d=out/folder;d.mkdir(parents=True,exist_ok=True)
 rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=d)
 (d/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
 for x in rows:
  r=x['result'];print(folder,x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
name='o15_384C_0239';base=Path('work/takeover/phase-next/s15-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
start=b.index('    if (g_5A97 & 1)');split=b.index('    win_GetObjRect(0x2101');stop=b.index('    for (;;)')
for phase,scope,shadow in itertools.product(['border','print','both'],[False,True],[False,True]):
 bb=b;first=b[start:split];second=b[split:stop]
 if phase in ['border','both']:
  if scope:first=first.replace('if (g_5A97 & 1) {','if (g_5A97 & 1) {\n        struct Rect '+('r' if shadow else 'borderRect')+';')
  else:bb=bb.replace('    struct Rect r;', '    struct Rect r;\n    struct Rect borderRect;')
  if not shadow or not scope:first=re.sub(r'\br\b','borderRect',first)
 if phase in ['print','both']:
  if scope:second='    {\n    struct Rect '+('r' if shadow else 'textRect')+';\n'+second+'    }\n'
  else:bb=bb.replace('    struct Rect r;', '    struct Rect r;\n    struct Rect textRect;')
  if not shadow or not scope:second=re.sub(r'\br\b','textRect',second)
 bb=bb.replace(b[start:stop],first+second)
 # When both phases have their own real rectangle, remove the now-unused original declaration.
 if phase=='both':bb=bb.replace('    struct Rect r;\n','',1)
 t=base[:f.body.s]+bb+base[f.body.e:]
 if any(t==v[1] for v in vs):continue
 vs.append((f'{phase}-scope{scope}-shadow{shadow}',t,''))
run(name,base,vs,'s15-rect-phases')
name='f_171C_0CF4';base=Path('work/takeover/phase-next/memory-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
for moved_ty,seg_ty,how in itertools.product(['int','unsigned','unsigned long'],['unsigned long','long'],['cast','word','volatile-word']):
 bb=b.replace('    unsigned seg;', '    '+seg_ty+' seg;').replace('    unsigned long moved;', '    '+moved_ty+' moved;')
 if moved_ty!='unsigned long':bb=bb.replace('return *(int near *)&moved;', 'return (int)moved;')
 at=bb.index('    moved = 0;');prefix=bb[:at];tail=bb[at:]
 if how=='cast':
  tail=tail.replace('(seg = (unsigned)SEG(b))','(unsigned)(seg = (unsigned)SEG(b))').replace('b->paras + seg','b->paras + (unsigned)seg')
 else:
  ref='(*(unsigned '+('volatile ' if how=='volatile-word' else '')+'near *)&seg)'
  tail=re.sub(r'\bseg\b',ref,tail)
 bb=prefix+tail
 vs.append((moved_ty.replace(' ','-')+'-'+seg_ty.replace(' ','-')+'-'+how,base[:f.body.s]+bb+base[f.body.e:],''))
run(name,base,vs,'memory-wide-segment')
