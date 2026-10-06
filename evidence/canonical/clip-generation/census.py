"""Read-only source call census; indirect calls are explicitly separate debt."""
from pathlib import Path
import re, json, collections, sys
sys.dont_write_bytecode = True
ROOT=next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
def functions():
    sys.path.insert(0,str(ROOT/'tools'))
    import csrc
    result={}
    for p in (ROOT/'src').rglob('*.c'):
        text=p.read_text(encoding='utf-8')
        for fn in csrc.Source(text).functions():
            calls=[]; indirect=[]
            for node in csrc.walk(fn.body):
                if isinstance(node,csrc.Call):
                    row={'line':text.count('\n',0,node.s)+1,'arguments':[text[a.s:a.e] for a in node.args]}
                    if isinstance(node.f,csrc.Id):
                        calls.append({'name':node.f.name,**row})
                    else:
                        indirect.append({'target':text[node.f.s:node.f.e],**row})
            if fn.name in result:
                raise ValueError('Duplicate C definition: '+fn.name)
            result[fn.name]={'path':p.relative_to(ROOT).as_posix(),'line':text.count('\n',0,fn.params_s)+1,'end':text.count('\n',0,fn.e)+1,'calls':calls,'indirect':indirect,'body':text[fn.body.s:fn.body.e]}
    return result
def collect():
    fs=functions(); code=json.loads((ROOT/'layout/symbols.json').read_text())['code']
    def alias(n):
        seen=set()
        while code.get(n,{}).get('alias_of') and n not in seen:
            seen.add(n); n=code[n]['alias_of']
        return n
    roots={'win_Open','win_Swap','win_DoProxMenu','f_20E8_0725'}
    census=[]
    for name,row in fs.items():
        for call in row['calls']:
            if alias(call['name']) in roots:
                census.append({'function':name,'path':row['path'],**call,'canonical':alias(call['name'])})
    transient={r['function'] for r in census}-{ 'YardToMap','MapToYard','OpenMapYard','OpenMapWindow','OpenEditWindow','OpenInfoWindow','OpenHistoryWindow','OpenCasteWindow','OpenModeWindow','NewGame','win_Open','win_Swap','f_20E8_0725','f_218D_0451','SetDefaultWindows','SetMapPlane','o22_39C7_0EBC'}
    paths={}
    for root in sorted(transient):
        q=collections.deque([(root,[])]); seen={root}; found=[]
        while q:
            n,chain=q.popleft()
            for c in fs.get(n,{}).get('calls',[]):
                dest=alias(c['name']); item=[n,fs[n]['path'],c['line'],dest]
                if dest in roots:
                    found.append(chain+[item]); continue
                if dest in fs and dest not in seen:
                    seen.add(dest); q.append((dest,chain+[item]))
        paths[root]=found
    hooks=['f_00BA_0228','f_00BA_0211','f_00BA_01C3','f_0250_0EDA','o12_384C_1035','win_DrawYardWindow','win_DrawInfoWindow','win_DrawModeWindow','win_DrawCasteWindow','win_DrawHistoryWindow']
    hook_open_paths={}
    for root in hooks:
        seen={root}; q=collections.deque([(root,[])]); found=[]
        while q:
            n,chain=q.popleft()
            for c in fs.get(n,{}).get('calls',[]):
                dest=alias(c['name']); item=[n,fs[n]['path'],c['line'],dest]
                if dest in roots:
                    found.append(chain+[item]); continue
                if dest in fs and dest not in seen:
                    seen.add(dest); q.append((dest,chain+[item]))
        hook_open_paths[root]=found
    out={'scope':'All canonical C parsed with tools/csrc.py. Pointer dispatch requires manual review. Paths do not impose statement lifetimes.','function_count':len(fs),'open_census':census,'opener_descendant_paths':paths,'hook_open_paths':hook_open_paths,'indirect_calls':[{ 'function':n,'path':r['path'],**c} for n,r in fs.items() for c in r['indirect']]}
    return out
def main():
    out=collect()
    print(json.dumps({'functions':out['function_count'],'open_calls':len(out['open_census']),
        'hook_open_paths':out['hook_open_paths']},indent=2))
if __name__=='__main__': main()
