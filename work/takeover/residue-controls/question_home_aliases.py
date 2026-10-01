from pathlib import Path
import sys,json,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_1C62_0415';ctx=modctx.resolve(func=name);base=(ROOT/'build/workers/takeover/question-loop-order/v2.c').read_text()
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/question-home-aliases';out.mkdir(exist_ok=True);vs=[]
for counts in ['plain','both','first','second','fold_both','fold_first']:
 for coord in ['plain','v','h','both']:
  for typ in ['near','far']:
   bb=b
   if counts in ['both','first','second']:
    old='j < count';new='j < *(int '+typ+' *)&count'
    if counts=='both':bb=bb.replace(old,new)
    elif counts=='first':bb=bb.replace(old,new,1)
    else:
     at=bb.index('for (j = 0;');bb=bb[:at]+bb[at:].replace(old,new,1)
   elif counts.startswith('fold'):
    old='j < count';new='(unsigned)count >= 0 && j < count';bb=bb.replace(old,new,1) if counts.endswith('first') else bb.replace(old,new)
   if coord!='plain':
    for var in (['v','h'] if coord=='both' else [coord]):
     bb=bb.replace('    int '+var+';','')
     bb=re.sub(r'\b'+var+r'\b', '(*(int '+typ+' *)&'+var+')',bb)
     bb=bb.replace('{\n','{\n    int '+var+';\n',1)
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],counts,coord,typ))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
