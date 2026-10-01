from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='win_PrintStyleTextInRect';ctx=modctx.resolve(func=name)
base=autosearch.unscaffold(ctx.source.read_text(),name);f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
cond="text[end] == '\\n' || text[end] == '\\r'"
assert 'if ('+cond+')' in b
out=ROOT/'build/workers/takeover/printstyle-byte-cse';out.mkdir(exist_ok=True);vs=[]
exprs=['text[end]','(unsigned char)text[end]','((unsigned char far *)text)[end]','*(unsigned char far *)(text + end)']
for expr in exprs:
 for op in ['plain','>= 0','<= 255','< 256','> 255','< 0']:
  for life in ['plain','line','lineH','both']:
   cc=f"{expr} == '\\n' || {expr} == '\\r'"
   if op not in ['plain','> 255','< 0']:cc=f'((unsigned char){expr} {op}) && ({cc})'
   elif op in ['> 255','< 0']:cc=f'((unsigned char){expr} {op}) || ({cc})'
   bb=b.replace('if ('+cond+')','if ('+cc+')')
   if life in ['line','both']:bb=bb.replace('pos < len && line < firstLine + maxLines','pos < len && (unsigned)line >= 0 && line < firstLine + maxLines')
   if life in ['lineH','both']:bb=bb.replace('if (f_24AB_030B() > lineH)','if ((unsigned)lineH >= 0 && f_24AB_030B() > lineH)')
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],expr,op,life))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,expr,op,life),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'expr':expr,'op':op,'life':life,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
