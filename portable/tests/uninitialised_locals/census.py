from pathlib import Path
import sys,json,re,hashlib
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'portable'))
from canonical_native_abi import integer_frontend as f,scalar,lexical,tokenizer
from canonical_native_abi import uninitialised_locals as u

def canonical_census(cc='C:/msys64/mingw64/bin/gcc.exe'):
    rows=[];units=[]
    for unit in json.loads((ROOT/'src/program.json').read_text())['modules']:
        if unit['lang']!='c':continue
        path=unit['source'];raw=(ROOT/path).read_text(encoding='latin1');source=scalar.convert(lexical.expand_shared_headers(raw))
        source=re.sub(r'\binterrupt\b','',source);source=re.sub(r'\b_segment\b','uint16_t',source)
        source=re.sub(r'_asm\s*\{[^{}]*\}',lambda m:';'+'\n'*m[0].count('\n'),source,flags=re.S)
        source=re.sub(r'\b_based\s*\([^()]*\)','',source)
        for t in reversed(tokenizer.tokenize(source)):
            if t.kind=='asm':source=source[:t.s]+';'+'\n'*t.text.count('\n')+source[t.e:]
        pp,_=f.preprocess('#include <stdint.h>\n#include <stddef.h>\n'+source,path,cc,[ROOT/'include'])
        tree=f.c_parser.CParser().parse(pp,filename=path);found,decl=u.census(tree)
        rows.extend(dict(r,source=path) for r in found)
        units.append(dict(source=path,source_sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),declarations=decl))
    return rows,units


def converted_census(report):
    report_path=Path(report);report=json.loads(report_path.read_text());rows=[];units=[]
    for unit in report['canonical_TUs']:
        if unit['lang']!='c' or 'integer_expression_input' not in unit:continue
        filename=unit['generated'];source=Path(unit['integer_expression_input']).read_text(encoding='latin1')
        from canonical_native_abi import m1b73_event_source
        source,_=m1b73_event_source.adapt_caller_context(source,unit['source'])
        source,_=u.adapt_reference_residue(source,unit['source'])
        build=report_path.parent
        pp,_=f.preprocess(source,filename,report['application_link']['command'][0],[build/'include',ROOT/'include',ROOT,build,ROOT/'portable/whole_program'])
        tree=f.c_parser.CParser().parse(pp,filename=filename)
        analysis=f.Analyzer(filename)
        found,decl=u.census(tree,analysis.active)
        rows.extend(dict(r,source=unit['source']) for r in found)
        units.append(dict(source=unit['source'],declarations=decl))
    return rows,units

def gcc_census(report,out,levels=('O0','O2')):
    import subprocess,concurrent.futures
    report_path=Path(report);r=json.loads(report_path.read_text());out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    def run(pair):
        unit,opt=pair;cmd=[x for x in unit['compile']['command'] if x not in ('-flto','-ffat-lto-objects') and not re.fullmatch('-O[0-3sgzfast]+',x)]
        cmd[cmd.index('-o')+1]=str(out/(unit['module'].replace(':','_')+'-'+opt+'.o'))
        cmd+=['-'+opt,'-Wuninitialized','-Wmaybe-uninitialized','-fdiagnostics-format=json']
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
        if p.returncode:raise ValueError('GCC census compilation failed: '+unit['source']+' '+p.stderr)
        diagnostics=json.loads(p.stderr)
        return dict(source=unit['source'],module=unit['module'],optimization=opt,exit_code=p.returncode,command=cmd,diagnostics=diagnostics)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        runs=list(ex.map(run,[(unit,opt) for unit in r['canonical_TUs'] if unit['lang']=='c' and 'compile' in unit for opt in levels]))
    (out/'diagnostics.json').write_text(json.dumps(runs,indent=2)+'\n')
    warnings=[dict(source=run['source'],module=run['module'],optimization=run['optimization'],option=d['option'],message=d['message']) for run in runs for d in run['diagnostics'] if 'uninit' in d.get('option','')]
    version=subprocess.check_output([r['application_link']['command'][0],'--version'],text=True).splitlines()[0]
    return dict(compiler=version,compiled_TUs=len(runs)//len(levels),optimization_levels=list(levels),
                omitted_C_TUs=[dict(source=unit['source'],status=unit['status']) for unit in r['canonical_TUs'] if unit['lang']=='c' and 'compile' not in unit],warnings=warnings)

def main():
    import argparse
    from collections import Counter
    ap=argparse.ArgumentParser(description='Check the classified canonical and converted automatic-storage census, including GCC diagnostics.')
    ap.add_argument('--report',type=Path);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--candidates-only',action='store_true')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    rows,units=canonical_census();result=dict(sites=rows,units=units)
    if args.report:
        result['converted_sites'],result['converted_units']=converted_census(args.report)
        result['gcc']=gcc_census(args.report,args.out/'gcc')
    if not args.candidates_only:
        expected=json.loads((ROOT/'evidence/canonical/uninitialised-locals/census.json').read_text())
        u.verify(rows,expected['sites'])
        if units!=expected['units']:raise ValueError('automatic-storage declaration/source census drift')
        if args.report:
            u.verify(result['converted_sites'],expected['converted_sites'])
            if result['converted_units']!=expected['converted_units']:raise ValueError('converted automatic declarations drift')
            if result['gcc']!=expected['gcc']:raise ValueError('unclassified GCC automatic-storage warning or compiler/inventory drift')
        result['passed']=True
    (args.out/'census.json').write_text(json.dumps(result,indent=2)+'\n');print(len(units),'canonical TUs;',len(rows),'candidate sites;',len(result.get('converted_sites',[])),'converted sites')
if __name__=='__main__':main()
