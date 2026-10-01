from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_171C_09CC';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/mem09-return-flag';out.mkdir(exist_ok=True);vs=[];meta=[]
for flow,call,typ,position in itertools.product(['all_returns','failure_exit','success_exit','direct_values','return_assignment'],['nested','argument'],['int','unsigned'],['first','last']):
 bb=b
 decl='    '+typ+' result;\n'
 if position=='first':bb=bb.replace('{\n','{\n'+decl,1)
 else:bb=bb.replace('    Block far *next;','    Block far *next;\n'+decl.rstrip())
 if call=='argument':bb=bb.replace('f_171C_068C(f_171C_0160(b, 0), paras, type);','f_171C_068C(b = f_171C_0160(b, 0), paras, type);')
 if flow=='all_returns':
  bb=bb.replace('            return 1;', '            { result = 1; goto done; }').replace('            return 0;', '            { result = 0; goto done; }').replace('    return 1;\n}', '    result = 1;\ndone:\n    return result;\n}')
 elif flow=='failure_exit':
  bb=bb.replace('    b = HDR(h);','    result = 0;\n    b = HDR(h);').replace('            return 0;', '            goto done;').replace('    return 1;\n}', '    result = 1;\ndone:\n    return result;\n}')
 elif flow=='success_exit':
  bb=bb.replace('    b = HDR(h);','    result = 1;\n    b = HDR(h);').replace('            return 1;', '            goto done;').replace('    return 1;\n}', 'done:\n    return result;\n}')
 elif flow=='direct_values':
  bb=bb.replace('return 1;', '{ result = 1; return result; }').replace('return 0;', '{ result = 0; return result; }')
 else:
  bb=bb.replace('return 1;', 'return result = 1;').replace('return 0;', 'return result = 0;')
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([flow,call,typ,position])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
