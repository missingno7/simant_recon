from pathlib import Path
import sys,json,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_2815_0165';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/adlib-volume-stages';out.mkdir(exist_ok=True);vs=[]
for level in ['param','register_param','local','register_local','local_fold','local_split_fold']:
 for factor in ['plain','char_mask','uchar_mask','char_separate','uchar_separate','char_xor','uchar_xor','char_factor']:
  bb=b;head=base[:f.body.s]
  if level=='register_param':head=head.replace('int vol, int voice)','register int vol, int voice)')
  elif level!='param':
   bb=re.sub(r'\bvol\b','level',bb)
   bb=bb.replace('{\n','{\n    '+('register int' if level=='register_local' else 'int')+' level;\n',1)
   bb=bb.replace('    level += fd_50F6_4B16;','    level = vol + fd_50F6_4B16;')
   if level in ['local_fold','local_split_fold']:
    bb=bb.replace('    p = fd_50F6_0000[instr].p;', '    if ((unsigned)level >= 0)\n        p = fd_50F6_0000[instr].p;')
   if level=='local_split_fold':bb=bb.replace('    level += *(int far *)(p + 0xd);','    if ((unsigned)level >= 0)\n        level += *(int far *)(p + 0xd);')
  if factor!='plain':
   typ='unsigned char' if factor.startswith('uchar') else 'char'
   bb=bb.replace('    unsigned char far *p;','    unsigned char far *p;\n    '+typ+' attenuation;')
   if factor.endswith('mask'):init='    attenuation = p[2] & 0x3f;\n    attenuation ^= 0x3f;\n'
   elif factor.endswith('separate'):init='    attenuation = p[2];\n    attenuation &= 0x3f;\n    attenuation ^= 0x3f;\n'
   elif factor.endswith('xor'):init='    attenuation = p[2] ^ 0x3f;\n    attenuation &= 0x3f;\n'
   else:init='    attenuation = (p[2] & 0x3f) ^ 0x3f;\n'
   bb=bb.replace('    f_283E_000A(g_6912',init+'    f_283E_000A(g_6912',1).replace('((p[2] & 0x3f) ^ 0x3f)','attenuation')
  n='v'+str(len(vs));vs.append((n,head+bb+base[f.body.e:],level,factor))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
