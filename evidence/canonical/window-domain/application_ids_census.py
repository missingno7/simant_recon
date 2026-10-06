"""Recheck reviewed symbolic writers and calls for three application ID roots."""
from pathlib import Path
import json,re,sys
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
sys.path.insert(0,str(ROOT/'tools'))
import csrc,behavior as b
ALIASES={'CurExpTool':'CurExpTool','fd_50F6_104C':'CurExpTool',
    'ExpSubStates':'ExpSubStates','fd_3D57_07B6':'ExpSubStates','fd_3D57_07BE':'scent_state'}
def collect():
 program=json.loads((ROOT/'src/program.json').read_text())
 reviewed_aliases=[]
 for alias,target in [('fd_50F6_104C','CurExpTool'),('fd_3D57_07B6','ExpSubStates')]:
  found=[x for x in program['aliases'] if x['alias']=='_'+alias]
  assert len(found)==1 and found[0]['kind']=='data' and found[0]['target']=='_'+target and found[0]['offset']==0
  reviewed_aliases.append({key:found[0][key] for key in ('alias','target','offset','kind')})
 rows=[];calls=[]
 for path in sorted((ROOT/'src').rglob('*.c')):
  text=path.read_text(); source=csrc.Source(text)
  for fn in source.functions():
   for node in csrc.walk(fn.body):
    if isinstance(node,csrc.Assign):
     ids=[x.name for x in csrc.walk(node.l) if isinstance(x,csrc.Id) and x.name in ALIASES]
     if ids:
      rows.append({'source':path.relative_to(ROOT).as_posix(),'function':fn.name,
        'root':ALIASES[ids[0]],'expression':text[node.s:node.e]})
    if isinstance(node,csrc.Call) and isinstance(node.f,csrc.Id) and node.f.name in ('SetExpTool','win_DoProxMenu','_win_SetProxItem','DoExpMenu'):
     calls.append({'source':path.relative_to(ROOT).as_posix(),'function':fn.name,
       'callee':node.f.name,'arguments':[text[x.s:x.e] for x in node.args]})
 text=(ROOT/'src/S09/m35F5.c').read_text()
 table=text[text.index('struct SaveRec far fd_4E4B_0000[308] ='):]
 records=[]
 for match in re.finditer(r'\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void far \*\)\s*([^}]+)\}',table):
  size,count=map(int,match.group(1,2));expr=match.group(3).strip()
  # Resolve every serialized pointer spelling, including symbol + literal.
  clean=expr.replace('&','').strip()
  add=0
  if clean.startswith('(') and clean.endswith(')'): clean=clean[1:-1]
  parts=clean.split('+')
  if len(parts)>2: raise ValueError(expr)
  name=parts[0].strip()
  if len(parts)==2: add=int(parts[1],0)
  address=b.symbol_address(name)+add
  records.append({'size':size,'count':count,'expression':expr,'address':address,'bytes':size*count})
 assert len(records)==307,len(records)
 spans={name:(b.symbol_address(name),width) for name,width in [('CurExpTool',2),('ExpSubStates',8),('fd_3D57_07BE',2)]}
 coverage={name:[{k:v for k,v in row.items() if k!='address'} for row in records if row['address']<at+width and at<row['address']+row['bytes']] for name,(at,width) in spans.items()}
 result={'data_aliases':reviewed_aliases,'writers':rows,'calls':calls,'save_record_count':len(records),'save_coverage':coverage}
 return result

if __name__=='__main__':
 result=collect()
 print(json.dumps(result,indent=2))
