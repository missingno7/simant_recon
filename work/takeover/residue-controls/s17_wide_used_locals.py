from pathlib import Path
import sys,json,itertools,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o17_384C_0039';ctx=modctx.resolve(func=name);base=(ROOT/'work/takeover/residue-controls/s17-parameter-width-v0.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/s17-wide-used-locals';out.mkdir(exist_ok=True);vs=[]
for local,typ,view in itertools.product(['index','object'],['long','unsigned long'],['plain','word','low_word','word_update']):
 bb=b
 if local=='index':
  bb=bb.replace('int i;',typ+' i;')
  if view in ['word','low_word','word_update']:
   use='(int)i' if view!='low_word' else '*(int near *)&i'
   bb=bb.replace('fd_50F6_46A8[i]', 'fd_50F6_46A8['+use+']').replace('fd_50F6_46BC[i]','fd_50F6_46BC['+use+']').replace('i - 0x200', '('+use+') - 0x200')
  if view=='word_update':bb=bb.replace('i++, r++','*(unsigned near *)&i += 1, r++')
 else:
  bb=bb.replace('    int i;', '    int i;\n    '+typ+' object;').replace('    h = db_LoadObject(id, 6);', '    object = id;\n    h = db_LoadObject(object, 6);').replace('db_UnhookObject(id, 6)', 'db_UnhookObject(object, 6)')
  if view=='word':bb=bb.replace('db_LoadObject(object,','db_LoadObject((int)object,').replace('db_UnhookObject(object,','db_UnhookObject((int)object,')
  if view in ['low_word','word_update']:bb=bb.replace('db_LoadObject(object,','db_LoadObject(*(int near *)&object,').replace('db_UnhookObject(object,','db_UnhookObject(*(int near *)&object,')
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],local,typ,view))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
