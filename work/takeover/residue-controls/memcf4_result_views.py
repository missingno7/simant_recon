from pathlib import Path
import sys,json,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0CF4';ctx=modctx.resolve(func=name);base=(ROOT/'build/workers/takeover/memcf4-result-lifetime/v6.c').read_text()
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/memcf4-result-views';out.mkdir(exist_ok=True);vs=[]
for view in ['low_alias','far_alias','union_long','union_ulong','union_bits_first','union_int','low_initial']:
 for life in ['plain','outer','type','copy','done','return']:
  bb=b
  if view.startswith('union'):
   bb=bb.replace('    unsigned long moved;','')
   bb=re.sub(r'\bmoved\b','result.bits',bb)
   ty='long' if view=='union_long' else 'unsigned long'
   fields=(ty+' bits; unsigned value;') if view=='union_bits_first' else (('int' if view=='union_int' else 'unsigned')+' value; '+ty+' bits;')
   bb=bb.replace('{\n','{\n    union { '+fields+' } result;\n',1).replace('*(int near *)&result.bits','result.value')
   expr='result.bits';word='result.value'
  else:
   expr='moved';word='*(unsigned near *)&moved'
   if view=='far_alias':bb=bb.replace('*(int near *)&moved','*(int far *)&moved')
   if view=='low_initial':bb=bb.replace('moved = 0;', '*(unsigned near *)&moved = 0;')
  fold='(unsigned)('+word+') >= 0'
  if life=='outer':bb=bb.replace('(seg = (unsigned)SEG(b)) < end', '('+fold+' && (seg = (unsigned)SEG(b)) < end)')
  elif life=='type':bb=bb.replace('if (b->type != 0x80)', 'if ('+fold+' && b->type != 0x80)')
  elif life=='copy':bb=bb.replace('        paras = n->paras;', '        if ('+fold+')\n            paras = n->paras;')
  elif life=='done':bb=bb.replace(expr+' = 1;', 'if ('+fold+') '+expr+' = 1;')
  elif life=='return':bb=bb.replace('return ', 'return '+fold+' ? ',1).replace(';\n}', ' : 0;\n}')
  n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],view,life))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
