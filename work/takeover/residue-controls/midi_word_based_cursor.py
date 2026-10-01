from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_284A_0138';text=autosearch.unscaffold((ROOT/'src/root/m284A.c').read_text(),name);f=csrc.Source(text).function(name);head=text[f.head_s:f.body.s];out=ROOT/'build/workers/takeover/midi-word-based-cursor';out.mkdir(exist_ok=True);vs=[]
for sign,bodykind in itertools.product(['unsigned char','char'],range(4)):
 h=head.replace('int off',sign+' _based(g_8DFC) *off')
 if bodykind==0:bb='{\n    return ((unsigned char _based(g_8DFC) *)off)[0] * 256 + ((unsigned char _based(g_8DFC) *)off)[1];\n}'
 elif bodykind==1:bb='{\n    union { unsigned word; struct { unsigned char lo, hi; } bytes; } result;\n    result.word = SONG(off);\n    result.bytes.hi = result.bytes.lo;\n    result.bytes.lo = SONG(off + 1);\n    return result.word;\n}'
 else:
  bb='{\n    unsigned high;\n    union { unsigned word; struct { unsigned char lo, hi; } bytes; } result;\n    high = SONG(off);\n    '+('if (high >= 0) ' if bodykind==3 else '')+'result.bytes.lo = SONG(off + 1);\n    result.bytes.hi = high;\n    return result.word;\n}'
 vs.append(text[:f.head_s]+h+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
