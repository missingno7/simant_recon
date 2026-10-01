from pathlib import Path
import sys,json,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_0250_129E';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/mapdraw-coordinate-copies';out.mkdir(exist_ok=True);vs=[]
for copy in ['x','y','xy']:
 for typ in ['int','unsigned','long']:
  for expr in ['plain','copied_all','inline_ay','indexed_pointer']:
   bb=b
   for v in (['x','y'] if copy=='xy' else [copy]):
    if expr!='plain':bb=re.sub(r'(?<!\.)\b'+v+r'\b', 'screen'+v.upper(),bb)
    bb=bb.replace('    int ay;', '    int ay;\n    '+typ+' screen'+v.upper()+';')
    bb=bb.replace('    ay =', '    screen'+v.upper()+' = '+v+';\n    ay =',1)
    if typ!='int':bb=re.sub(r'(?<![.\w])screen'+v.upper()+r'(?=\b)', '(int)screen'+v.upper(),bb)
    # Restore declaration and assignment lvalue after the word-consumer casts.
    bb=bb.replace(typ+' (int)screen'+v.upper()+';',typ+' screen'+v.upper()+';').replace('(int)screen'+v.upper()+' = '+v+';', 'screen'+v.upper()+' = '+v+';')
   if expr=='plain':continue
   if expr=='inline_ay':bb=bb.replace('if (ay > 0x3f)', 'if ((fd_50F6_0508.y + '+('(int)screenY' if 'y' in copy and typ!='int' else 'screenY' if 'y' in copy else 'y')+') > 0x3f)')
   if expr=='indexed_pointer':bb=bb.replace('p = &fd_50F6_15C4[0][i];','p = fd_50F6_15C4[0] + i;')
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],copy,typ,expr))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
