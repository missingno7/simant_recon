from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0ADC';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/memadc-pointer-types';out.mkdir(exist_ok=True);vs=[]
for segtype in ['unsigned long','volatile unsigned long','long','volatile long','unsigned','volatile unsigned']:
 for pointer in ['direct','local','ulong_local']:
  for null in ['plain','segment']:
   bb=b.replace('unsigned long seg;',segtype+' seg;')
   if null=='segment':bb=bb.replace('if (n)', 'if (SEG(n))')
   expr='(char far *)((unsigned long)b + 0x20000L)'
   if pointer!='direct':
    decl='    '+('char far *data;' if pointer=='local' else 'unsigned long data;')+'\n'
    bb=bb.replace('    '+segtype+' seg;\n','    '+segtype+' seg;\n'+decl)
    bb=bb.replace('    *(Handle)((char far *)s_2F46 + b->handle) = '+expr+';', '    data = '+(expr if pointer=='local' else '(unsigned long)b + 0x20000L')+';\n    *(Handle)((char far *)s_2F46 + b->handle) = '+('data' if pointer=='local' else '(char far *)data')+';')
   vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
for var in ['seg','b','n']:
 for site in ['next_call','prev','next','null']:
  if var=='n' and site!='null':continue
  bb=b;cond='((unsigned long)'+var+' >= 0)'
  if site=='next_call':bb=bb.replace('    f_194D_0006(', '    if ('+cond+') f_194D_0006(')
  elif site=='prev':bb=bb.replace('if (b->prev)', 'if (b->prev && '+cond+')')
  elif site=='next':bb=bb.replace('if (b->next)', 'if (b->next && '+cond+')')
  else:bb=bb.replace('if (n)', 'if (SEG(n) && '+cond+')')
  vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
