from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_0250_129E';ctx=modctx.resolve(func=name)
base=(ROOT/'build/workers/takeover/mapdraw-coordinate-copies/v9.c').read_text()
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/mapdraw-sum-cse';out.mkdir(exist_ok=True);vs=[]
s='(fd_50F6_0508.y + screenY)'
for decl,form in itertools.product(['keep','remove'],['unsigned0','unsigned_max','ulong0','ulong_max','xor_self','and_zero','duplicate_x','duplicate_y','comma_fold','void_read','negative_fold','long_signed']):
 bb=b.replace('    ay = fd_50F6_0508.y + screenY;\n','').replace('if (ay > 0x3f)', 'if ('+s+' > 0x3f)')
 if decl=='remove':bb=bb.replace('    int ay;\n','')
 bound='x < 0 || screenY < 0 || x >= 40 || screenY >= 30'
 forms={'unsigned0':'(unsigned)'+s+' < 0 || '+bound,'unsigned_max':'(unsigned)'+s+' > 65535U || '+bound,'ulong0':'(unsigned long)(unsigned)'+s+' < 0 || '+bound,'ulong_max':'(unsigned long)(unsigned)'+s+' > 65535UL || '+bound,'xor_self':'('+s+' ^ '+s+') || '+bound,'and_zero':'('+s+' & 0) || '+bound,'duplicate_x':'('+s+' > 63 && x < 0) || '+bound,'duplicate_y':'('+s+' > 63 && screenY < 0) || '+bound,'comma_fold':'((unsigned)'+s+' >= 0, x < 0) || screenY < 0 || x >= 40 || screenY >= 30','void_read':bound,'negative_fold':'!((unsigned)'+s+' >= 0) || '+bound,'long_signed':'(long)'+s+' < -32768L || '+bound}
 bb=bb.replace('if ('+bound+')','if ('+forms[form]+')')
 if form=='void_read':bb=bb.replace('    if (x < 0','    (void)'+s+';\n    if (x < 0',1)
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],decl,form))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
