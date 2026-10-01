from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='win_PrintStyleTextInRect';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
cond="text[end] == '\\n' || text[end] == '\\r'";old="        while (text[end] == ' ')\n            end++;\n        if ("+cond+")\n            end++;"
assert old in b
out=ROOT/'build/workers/takeover/printstyle-char-ranges';out.mkdir(exist_ok=True);vs=[]
checks=['text[end] >= -128','text[end] <= 127','text[end] < 128','text[end] > -129','(unsigned long)text[end] >= 0','(unsigned long)text[end] <= 0xffffffffUL','(unsigned)end >= 0','(unsigned long)end >= 0']
for check in checks:
 for place in ['before','after','while','block','ifelse']:
  for order in ['plain','pos_first']:
   bb=b
   if order=='pos_first':bb=bb.replace('    int len;\n    int pos;', '    int pos;\n    int len;')
   if place=='before':bb=bb.replace('if ('+cond+')','if ('+check+' && ('+cond+'))')
   elif place=='after':bb=bb.replace('if ('+cond+')','if (('+cond+') && '+check+')')
   elif place=='while':bb=bb.replace("while (text[end] == ' ')","while ("+check+" && text[end] == ' ')")
   elif place=='block':bb=bb.replace(old,'        if ('+check+') {\n'+old+'\n        }')
   else:bb=bb.replace('if ('+cond+')\n            end++;','if (text[end] == \'\\n\')\n            end++;\n        else if ('+check+' && text[end] == \'\\r\')\n            end++;')
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],check,place,order))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
