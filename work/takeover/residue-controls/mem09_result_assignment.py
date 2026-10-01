from pathlib import Path
import sys,json,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_09CC';ctx=modctx.resolve(func=name)
base=(ROOT/ctx.source).read_text();old=(ROOT/'work/takeover/full-search/f_171C_09CC/best.c').read_text()
f=csrc.Source(base).function(name);of=csrc.Source(old).function(name)
b=old[of.body.s:of.body.e];base=autosearch.unscaffold(base,name);f=csrc.Source(base).function(name)
out=ROOT/'build/workers/takeover/mem09-result-assignment';out.mkdir(exist_ok=True);vs=[]
for call in ['nested','assignment','comma','argument_assignment']:
 for para in ['plain','int','register','local','local_register']:
  for fold in ['none','first','last','return','call']:
   bb=b
   if call=='assignment':bb=bb.replace('f_171C_068C(f_171C_0160(b, 0), paras, type);','b = f_171C_0160(b, 0);\n    f_171C_068C(b, paras, type);')
   elif call=='comma':bb=bb.replace('f_171C_068C(f_171C_0160(b, 0), paras, type);','b = f_171C_0160(b, 0), f_171C_068C(b, paras, type);')
   elif call=='argument_assignment':bb=bb.replace('f_171C_0160(b, 0)','b = f_171C_0160(b, 0)')
   if fold=='first':bb=bb.replace('b->paras > paras','((unsigned)paras >= 0) && b->paras > paras')
   elif fold=='last':bb=bb.replace('next->paras + b->paras < paras','(next->paras + b->paras < paras && (unsigned)paras >= 0)')
   elif fold=='return':bb=bb.replace('return 1;', 'return (unsigned)paras >= 0;')
   elif fold=='call':bb=bb.replace('    f_171C_068C(', '    if ((unsigned)paras >= 0) f_171C_068C(')
   head=base[:f.body.s]
   if para=='register':head=head[:f.head_s]+head[f.head_s:].replace('unsigned paras','register unsigned paras')
   elif para=='int':head=head[:f.head_s]+head[f.head_s:].replace('unsigned paras','int paras')
   elif para.startswith('local'):
    bb=re.sub(r'(?<!>)\bparas\b','amount',bb).replace('{\n','{\n    '+('register ' if para=='local_register' else '')+'unsigned amount;\n',1)
    bb=bb.replace('    b = HDR(h);','    amount = paras;\n    b = HDR(h);')
   vs.append(('v'+str(len(vs)),head+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
