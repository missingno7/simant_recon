from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_20E8_0903';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/windowrect-address-locals';out.mkdir(exist_ok=True);vs=[]
for ptr in ['normal','register','const','char']:
 for assign in ['before_condition','inside_arms','inline_arms']:
  for index in ['add','index']:
   bb=b.replace('    int i;', '    int i;\n    '+{'normal':'int far *','register':'register int far *','const':'int far * const ','char':'char far *'}[ptr]+'dest;')
   addr=('*((int far * far *)&origin) + i' if False else ('origin + i' if index=='add' else '&origin[i]'))
   if ptr=='char':addr='(char far *)('+addr+')'
   use='*(int far *)dest' if ptr=='char' else '*dest'
   if assign=='before_condition':
    bb=bb.replace('for (i = 0; i < 4; i++) {','for (i = 0; i < 4; i++) {\n        dest = '+addr+';')
    bb=bb.replace('origin[i]',use)
   elif assign=='inside_arms':
    bb=bb.replace('origin[i] = 0;', '{ dest = '+addr+'; '+use+' = 0; }')
    bb=bb.replace('origin[i] = rect[i] - o[i];', '{ dest = '+addr+'; '+use+' = rect[i] - o[i]; }')
   else:bb=bb.replace('origin[i]', '*'+('(int far *)' if ptr=='char' else '')+'(dest = '+addr+')')
   if ptr=='const':continue # assignments to a const pointer are invalid
   for proto in ['original','unnamed','future','both']:
    tt=base[:f.body.s]+bb+base[f.body.e:]
    if proto in ['unnamed','both']:tt=tt.replace('f_2505_02D7(int obj);','f_2505_02D7(int);')
    if proto in ['future','both']:
     decl='extern int far f_2505_036E(void);';tt=tt.replace(decl,'');pos=csrc.Source(tt).function(name).head_s;tt=tt[:pos]+decl+'\n'+tt[pos:]
    vs.append(('v'+str(len(vs)),tt))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
