from pathlib import Path
import sys,json,re,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='LessonDone';ctx=modctx.resolve(func=name);base=(ROOT/'build/workers/takeover/lesson-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/lesson-boolean-returns';out.mkdir(exist_ok=True);vs=[]
for group,last,fall in itertools.product(['all','simple','calls','eq','multi','not_calls'],['plain','break'],[False,True]):
 bb=b
 if fall:
  for i in [8,43,46,50]:bb=re.sub(r'    case '+str(i)+r':\n.*?(?=    case |    }\n    return)', '',bb,flags=re.S)
  bb=bb.replace('    case 30:\n', '    case 30:\n').replace('        if (fd_50F6_1074 != 0)\n            return 1;\n        break;\n    case 31:', ''.join('    case '+str(i)+':\n' for i in [8,43,46,50])+'        if (fd_50F6_1074 != 0)\n            return 1;\n        break;\n    case 31:')
 def repl(m):
  cond=m.group(1);call='f_' in cond;multi='&&' in cond or '||' in cond
  use=group=='all' or group=='simple' and not multi or group=='calls' and call or group=='eq' and ('==' in cond or '!=' in cond) and not multi or group=='multi' and multi or group=='not_calls' and not call
  return '        return '+cond+';\n' if use else m.group(0)
 bb=re.sub(r'        if \(([^{}\n]*(?:\n[^{}\n]*)?)\)\n            return 1;\n        break;\n',repl,bb)
 if last=='break':bb=bb.replace('        return 0;\n    case 55:', '        break;\n    case 55:')
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],group,last,fall))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
