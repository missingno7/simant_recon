from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='o15_384C_0239';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/s15-text-components';out.mkdir(exist_ok=True);vs=[]
for typ,segtyp,order,representation in itertools.product(['unsigned','register unsigned'],['unsigned','_segment'],[False,True],['bits','based']):
 bb=b.replace('    char far *text;', '    char far *raw;\n    '+typ+' textOff;\n    '+segtyp+' textSeg;')
 assignments=['textOff = (unsigned)raw;', 'textSeg = ('+segtyp+')((unsigned long)raw >> 16);']
 if order:assignments.reverse()
 bb=bb.replace('text = f_171C_1B84(h);','raw = f_171C_1B84(h);\n    '+'\n    '.join(assignments))
 value='(char far *)(((unsigned long)textSeg << 16) | textOff)' if representation=='bits' else '(char _based(textSeg) *)textOff'
 bb=bb.replace('win_PrintTextInRect(0, text, &r);','win_PrintTextInRect(0, '+value+', &r);')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
