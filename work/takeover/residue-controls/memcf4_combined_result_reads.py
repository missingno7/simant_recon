from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0CF4';ctx=modctx.resolve(func=name)
base=(ROOT/'build/workers/takeover/memcf4-result-lifetime/v6.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/memcf4-combined-result-reads';out.mkdir(exist_ok=True);vs=[]
for mask in range(64):
 bb=b;fold='(unsigned)(*(unsigned near *)&moved) >= 0'
 if mask&1:bb=bb.replace('(seg = (unsigned)SEG(b)) < end','('+fold+' && (seg = (unsigned)SEG(b)) < end)')
 if mask&2:bb=bb.replace('if (b->type != 0x80)', 'if ('+fold+' && b->type != 0x80)')
 if mask&4:bb=bb.replace('while ((unsigned)SEG(n) < end)', 'while ('+fold+' && (unsigned)SEG(n) < end)')
 if mask&8:bb=bb.replace('        paras = n->paras;', '        if ('+fold+')\n            paras = n->paras;')
 if mask&16:bb=bb.replace('moved = 1;', 'if ('+fold+') moved = 1;')
 if mask&32:bb=bb.replace('return *(int near *)&moved;', 'return '+fold+' ? *(int near *)&moved : 0;')
 n='v'+str(mask);vs.append((n,base[:f.body.s]+bb+base[f.body.e:],mask))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,mask),r in zip(vs,ev.many([t for _,t,_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':[mask],**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
