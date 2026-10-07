"""Front-end census of consumed DOS return contracts, without changing sources.

GCC preprocessing + pycparser ASTs retain declarations, call expression parents,
and control-flow exits. Parse failures and indirect calls remain explicit debt.
The parse-only headers are generated in the ignored output, never compiled.
"""
from pathlib import Path
import argparse
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'build/deps/pycparser'))
sys.path.insert(0, str(ROOT / 'portable'))
import pycparser
from pycparser import c_ast as C, c_parser, c_generator
from canonical_native_abi import scalar, tokenizer
from canonical_native_abi.lexical import function_heads, rename, masked

GEN = c_generator.CGenerator()
FAKE = {
    'stdlib.h': '#include <stddef.h>\nvoid *malloc(size_t); void free(void *); void *realloc(void *,size_t); int abs(int); long labs(long); int atoi(const char *); void exit(int); void abort(void); int atexit(void (*)(void));\n',
    'string.h': '#include <stddef.h>\nvoid *memcpy(void *,const void *,size_t); void *memset(void *,int,size_t); int memcmp(const void *,const void *,size_t); size_t strlen(const char *); char *strcpy(char *,const char *); char *strcat(char *,const char *); int strcmp(const char *,const char *);\n',
    'dos.h': 'union REGS { struct { unsigned short ax,bx,cx,dx,si,di,cflag,flags; } x; struct { unsigned char al,ah,bl,bh,cl,ch,dl,dh; } h; }; struct SREGS { unsigned short es,cs,ss,ds; };\n#define _A_SUBDIR 16\n#define _A_NORMAL 0\n#define _A_RDONLY 1\n#define _A_HIDDEN 2\n#define _A_SYSTEM 4\n#define _A_ARCH 32\nint _dos_allocmem(unsigned short,unsigned short *); int _dos_freemem(unsigned short); int _dos_setblock(unsigned short,unsigned short,unsigned short *); int int86(int,union REGS *,union REGS *); int int86x(int,union REGS *,union REGS *,struct SREGS *);\n',
    'io.h': 'int open(const char *,int,...); int close(int); int read(int,void *,unsigned); int write(int,const void *,unsigned); long lseek(int,long,int); int access(const char *,int); int remove(const char *);\n',
    'direct.h': 'int chdir(const char *); char *getcwd(char *,int); int mkdir(const char *);\n',
    'fcntl.h': '#define O_RDONLY 0\n#define O_WRONLY 1\n#define O_RDWR 2\n#define O_BINARY 0x8000\n#define O_CREAT 0x100\n#define O_TRUNC 0x200\n',
    'time.h': 'typedef long time_t; typedef long clock_t; time_t time(time_t *); clock_t clock(void);\n',
    'sys/types.h': 'typedef unsigned short dev_t; typedef short ino_t; typedef unsigned short mode_t; typedef short nlink_t; typedef short uid_t; typedef short gid_t; typedef long off_t;\n',
    'sys/stat.h': '#include <sys/types.h>\nstruct stat { dev_t st_dev; ino_t st_ino; mode_t st_mode; nlink_t st_nlink; uid_t st_uid; gid_t st_gid; dev_t st_rdev; off_t st_size; long st_atime,st_mtime,st_ctime; }; int stat(const char *,struct stat *);\n',
    'stdint.h': '''#ifndef PARSE_STDINT
#define PARSE_STDINT
typedef signed char int8_t; typedef unsigned char uint8_t;
typedef signed short int16_t; typedef unsigned short uint16_t;
typedef signed int int32_t; typedef unsigned int uint32_t;
typedef signed long long int64_t; typedef unsigned long long uint64_t;
typedef unsigned long long uintptr_t; typedef signed long long intptr_t;
#define UINT16_C(x) x
#define INT16_C(x) x
#define UINT32_C(x) x##U
#define INT32_C(x) x
#define UINT64_C(x) x##ULL
#define INT64_C(x) x##LL
#define INT16_MIN (-32767-1)
#define INT16_MAX 32767
#define UINT16_MAX 65535
#define UINT32_MAX 4294967295U
#endif
''',
    'stddef.h': '''#ifndef PARSE_STDDEF
#define PARSE_STDDEF
typedef unsigned long long size_t; typedef signed long long ptrdiff_t;
#define NULL ((void *)0)
#define offsetof(t,m) ((size_t)0)
#endif
''',
    'stdarg.h': 'typedef void *va_list;\nvoid va_start(va_list,...); void va_end(va_list);\n',
    'stdio.h': '#include <stddef.h>\ntypedef struct ParseFILE FILE;\nint sprintf(char *,const char *,...); int printf(const char *,...);\n',
    'ctype.h': 'int islower(int); int toupper(int); int tolower(int); int isalpha(int); int isdigit(int); int isalnum(int); int isspace(int); int isupper(int);\n',
}
FAKE['string.h'] += 'unsigned short _fstrlen(const char *); char *_fstrrchr(const char *,int); int _fstrcmp(const char *,const char *); int _fmemcmp(const void *,const void *,unsigned); int _fstrncmp(const char *,const char *,unsigned);\n'
FAKE['dos.h'] += 'int _dos_findfirst(const char *,unsigned,struct find_t *); int _dos_findnext(struct find_t *);\n#define FP_SEG(p) ((unsigned short)(((uintptr_t)(p)) >> 16))\n'
FAKE['time.h'] += 'struct tm; struct tm *localtime(const time_t *); char *asctime(const struct tm *);\n'

def callable_type(t):
    while isinstance(t,(C.PtrDecl,C.ArrayDecl,C.TypeDecl)):
        t=t.type
    return t if isinstance(t,C.FuncDecl) else None

def nodes(node):
    if node is not None:
        yield node
        for _, child in node.children():
            yield from nodes(child)

def typename(t, typedefs, seen=()):
    if isinstance(t, C.TypeDecl):
        return typename(t.type, typedefs, seen)
    if isinstance(t, C.IdentifierType):
        name = ' '.join(t.names)
        if name in typedefs and name not in seen:
            return typename(typedefs[name], typedefs, seen + (name,))
        return name
    if isinstance(t, C.PtrDecl):
        return typename(t.type, typedefs, seen) + ' *'
    if isinstance(t, C.ArrayDecl):
        return typename(t.type, typedefs, seen) + ' *'
    if isinstance(t, C.FuncDecl):
        return 'function:' + typename(t.type, typedefs, seen)
    if isinstance(t, (C.Struct, C.Union)):
        return type(t).__name__.lower() + ':' + str(t.name)
    if isinstance(t, C.Enum):
        return 'enum:' + str(t.name)
    return type(t).__name__

def constant(node):
    if isinstance(node, C.Constant) and node.type in {'int', 'unsigned int'}:
        try: return int(re.sub('[uUlL]+$', '', node.value), 0)
        except ValueError: pass
    return None

class Flow:
    """Conservative CFG: labels/goto, switch/default, loops, break/continue.

    Unknown conditions keep both edges. A reachable bare return or end is an
    unspecified result. No guessed noreturn annotation removes failure paths.
    """
    def __init__(self):
        self.edges = defaultdict(set)
        self.next = 0
        self.labels = {}
        self.gotos = []
        self.bare_returns = []
        self.exit = self.new()

    def new(self, edges=()):
        ident = self.next; self.next += 1
        self.edges[ident].update(edges)
        return ident

    def build(self, node, follow, brk=None, cont=None, cases=None):
        if node is None: return follow
        if isinstance(node, C.Compound):
            start = follow
            for statement in reversed(node.block_items or []):
                start = self.build(statement, start, brk, cont, cases)
            return start
        if isinstance(node, C.Return):
            ident = self.new()
            if node.expr is None: self.bare_returns.append(ident)
            return ident
        if isinstance(node, C.Goto):
            ident = self.new(); self.gotos.append((ident, node.name)); return ident
        if isinstance(node, C.Label):
            start = self.build(node.stmt, follow, brk, cont, cases)
            self.labels[node.name] = start; return start
        if isinstance(node, C.Break): return self.new([brk] if brk is not None else [])
        if isinstance(node, C.Continue): return self.new([cont] if cont is not None else [])
        if isinstance(node, C.If):
            yes = self.build(node.iftrue, follow, brk, cont, cases)
            no = self.build(node.iffalse, follow, brk, cont, cases)
            value = constant(node.cond)
            return self.new([yes, no] if value is None else [yes if value else no])
        if isinstance(node, (C.While, C.DoWhile, C.For)):
            check = self.new()
            start = self.build(node.stmt, check, follow, check, cases)
            value = 1 if isinstance(node, C.For) and node.cond is None else constant(node.cond)
            self.edges[check].update([start, follow] if value is None else [start if value else follow])
            return start if isinstance(node, C.DoWhile) else check
        if isinstance(node, C.Switch):
            choices = []
            self.build(node.stmt, follow, follow, cont, choices)
            has_default = any(is_default for _, is_default in choices)
            return self.new([ident for ident, _ in choices] + ([] if has_default else [follow]))
        if isinstance(node, (C.Case, C.Default)):
            start = follow
            for statement in reversed(node.stmts or []):
                start = self.build(statement, start, brk, cont, cases)
            if cases is not None: cases.append((start, isinstance(node, C.Default)))
            return start
        return self.new([follow])

    def exits(self, body):
        start = self.build(body, self.exit)
        for ident, name in self.gotos:
            if name not in self.labels: raise ValueError('unknown goto label: ' + name)
            self.edges[ident].add(self.labels[name])
        seen = set(); pending = [start]
        while pending:
            ident = pending.pop()
            if ident in seen: continue
            seen.add(ident); pending.extend(self.edges[ident] - seen)
        return dict(fallthrough=self.exit in seen,
                    bare_return=any(i in seen for i in self.bare_returns))

def consumed(node, parent, field, ancestors):
    if any(isinstance(n, C.UnaryOp) and n.op in {'sizeof', '_Alignof'} for n in ancestors):
        return False
    if isinstance(parent, C.Compound): return False
    if isinstance(parent, (C.Case,C.Default)) and field == 'stmts': return False
    if isinstance(parent, C.If) and field in {'iftrue','iffalse'}: return False
    if isinstance(parent, (C.While,C.DoWhile,C.For,C.Label)) and field == 'stmt': return False
    if isinstance(parent, C.Cast) and GEN.visit(parent.to_type) == 'void': return False
    if isinstance(parent, C.For) and field in {'init', 'next'}: return False
    if isinstance(parent, C.ExprList):
        if ancestors and isinstance(ancestors[-1], C.FuncCall): return True
        if node is not parent.exprs[-1]: return False
        if ancestors and isinstance(ancestors[-1], C.Compound): return False
    return True

def analyze(tree, filename, source, canonical):
    typedefs = {n.name:n.type for n in tree.ext if isinstance(n, C.Typedef)}
    declarations = {}; definitions = {}; calls = []; indirect = []; pointer_types = {}; pointer_targets = {}
    own = lambda n: n.coord and n.coord.file.replace('\\', '/') == str(filename).replace('\\', '/')
    for n in tree.ext:
        decl = n.decl if isinstance(n, C.FuncDef) else n
        if isinstance(decl, C.Decl) and isinstance(decl.type, C.FuncDecl):
            declarations[decl.name] = typename(decl.type.type, typedefs)
            if isinstance(n, C.FuncDef) and own(n):
                definitions[decl.name] = dict(return_type=declarations[decl.name],
                    line=decl.coord.line, static='static' in decl.storage,
                    **Flow().exits(n.body))
        elif isinstance(decl,C.Decl) and callable_type(decl.type):
            pointer_types[decl.name]=typename(callable_type(decl.type).type,typedefs)
            if decl.init is not None:
                pointer_targets[decl.name]=[v.name for v in nodes(decl.init) if isinstance(v,C.ID)]
    def walk(n, parent=None, field='', ancestors=(), caller=None, local=None):
        if n is None: return
        if isinstance(n, C.FuncDef):
            caller = n.decl.name
            local = dict(declarations)
        if local is not None and isinstance(n, C.Decl) and isinstance(n.type, C.FuncDecl):
            local[n.name] = typename(n.type.type, typedefs)
        if isinstance(n,C.Decl) and not isinstance(n.type,C.FuncDecl) and callable_type(n.type):
            pointer_types[n.name]=typename(callable_type(n.type).type,typedefs)
        if isinstance(n, C.FuncCall) and own(n) and consumed(n,parent,field,ancestors):
            name = n.name.name if isinstance(n.name, C.ID) else None
            row = dict(caller=caller, line=n.coord.line, expression=GEN.visit(n),
                       declared_return=(local or declarations).get(name))
            if name in (local or declarations) and row['declared_return'] == 'void':
                pass  # A void expression statement cannot supply a consumed value.
            elif name in (local or declarations):
                row['callee'] = name; calls.append(row)
            else:
                target=n.name
                while isinstance(target,C.UnaryOp) and target.op=='*': target=target.expr
                if isinstance(target,C.ArrayRef): target=target.name
                if isinstance(target,C.ID) and target.name in pointer_types:
                    row['declared_return']=pointer_types[target.name]
                    row['target_kind']='function-pointer'
                    row['pointer_name']=target.name
                elif isinstance(target,C.Cast) and callable_type(target.to_type.type):
                    row['declared_return']=typename(callable_type(target.to_type.type).type,typedefs)
                    row['target_kind']='function-pointer-cast'
                else: row['target_kind']='undeclared-direct' if name else 'unresolved-indirect'
                if row['declared_return']!='void':
                    row['target'] = GEN.visit(n.name); indirect.append(row)
        for name, child in n.children():
            walk(child,n,name.split('[')[0],ancestors + ((parent,) if parent else ()),caller,local)
    walk(tree)
    heads = function_heads(source)
    qualifiers=r'\b(?:extern|static|far|near|pascal|_fastcall|_cdecl|__cdecl|_export|_loadds)\b'
    implicit = [h['name'] for h in heads if re.match(re.escape(h['name']) + r'\s*\(',re.sub(qualifiers,'',h['signature']).strip())]
    code=masked(source); depths=[]; depth=0
    for ch in code:
        depths.append(depth)
        if ch=='{': depth+=1
        elif ch=='}': depth-=1
    implicit += [m.group(1) for m in re.finditer(r'(?:^|[;{}])\s*(?:(?:extern|static|far|near|_fastcall|pascal)\s+)*([A-Za-z_]\w*)\s*\([^{};]*\)\s*;',code,re.M) if depths[m.start(1)]==0]
    implicit = sorted(set(implicit)&set(declarations))
    return dict(definitions=definitions, declarations=declarations, calls=calls,
                indirect=indirect, implicit_int=implicit,pointer_targets=pointer_targets)

def parse(source, filename, includes, fake, cc):
    command = [cc,'-E','-std=c11','-nostdinc','-D__attribute__(x)=','-D__extension__=',
               '-D_Static_assert(x,y)=','-I',str(fake)]
    for directory in includes: command += ['-I',str(directory)]
    command += ['-x','c','-']
    prefix = '#line 1 "' + str(filename).replace('\\','/') + '"\n'
    run = subprocess.run(command,input=prefix+source,capture_output=True,text=True,timeout=30)
    if run.returncode: raise ValueError(run.stderr)
    return c_parser.CParser().parse(run.stdout, filename=str(filename))

def canonical_parse_source(source):
    # Inline-ASM statements are opaque register code, not C return statements.
    # Macro-contained ASM is blanked after GCC expansion, below.
    source = scalar.convert(source)
    source = re.sub(r'\b_segment\b','uint16_t',source)
    source = re.sub(r'\b_based\s*\([^)]*\)','',source)
    return source

def scan(project, build, out, cc='C:/msys64/mingw64/bin/gcc.exe'):
    fake = out/'parse-headers'; fake.mkdir(parents=True,exist_ok=True)
    for name,text in FAKE.items():
        (fake/name).parent.mkdir(parents=True,exist_ok=True)
        (fake/name).write_text(text)
    report = json.loads((build/'report.json').read_text())
    inventory = json.loads((project/'src/program.json').read_text())
    aliases = {a['alias'].lstrip('_@'):a.get('target',a.get('owner')).lstrip('_@')
               for a in inventory['aliases'] if a['kind']=='code'}
    thunk=(project/'src/root/m2CFB.asm').read_text(encoding='latin1')
    aliases.update({a.lstrip('_@'):b.lstrip('_@') for a,b in re.findall(r'(?m)^\s*(\w+):\s+jmp\s+(\w+)\s*$',thunk)})
    for name,target in list(aliases.items()):
        seen=set()
        while target in aliases and target not in seen:
            seen.add(target); target=aliases[target]
        aliases[name]=target
    includes = [build/'include',project,build,project/'include',project/'portable/whole_program']
    work = []
    for row in report['canonical_TUs']:
        if row['lang'] != 'c': continue
        work.append((row,'native',Path(row['generated'])))
        work.append((row,'canonical',project/row['source']))
    def one(task):
        row,kind,path = task; source = path.read_text(encoding='latin1')
        try:
            if kind == 'canonical':
                # Preprocess once to expose macro inline ASM before lexical removal.
                pre = rename(canonical_parse_source(source),aliases)
                command = [cc,'-E','-std=c11','-nostdinc','-D__attribute__(x)=','-I',str(fake),'-I',str(project/'include'),'-x','c','-']
                run = subprocess.run(command,input='#include <stdint.h>\n#include <stddef.h>\n#line 1 "'+path.as_posix()+'"\n'+pre,capture_output=True,text=True,timeout=30)
                if run.returncode: raise ValueError(run.stderr)
                pre = run.stdout
                for t in reversed(tokenizer.tokenize(pre)):
                    if t.kind == 'asm':
                        pre = pre[:t.s] + ';' + '\n'*t.text.count('\n') + pre[t.e:]
                tree = c_parser.CParser().parse(pre,filename=str(path))
            else:
                tree = parse(source,path,includes,fake,cc)
            return dict(source=row['source'],kind=kind,module=row['module'],
                        compiled_native=row.get('status')!='PLATFORM_BOUNDARY',
                        sha256=hashlib.sha256(source.encode('latin1')).hexdigest(),
                        **analyze(tree,path,source,kind=='canonical'))
        except Exception as e:
            return dict(source=row['source'],kind=kind,module=row['module'],error=str(e))
    with ThreadPoolExecutor(max_workers=8) as pool: units = list(pool.map(one,work))
    asm = {}
    for row in inventory['modules']:
        if row['lang'] != 'asm': continue
        text=(project/row['source']).read_text(encoding='latin1')
        for name in re.findall(r'(?im)^\s*([\w@]+)\s+proc\b',text):
            asm[name.lstrip('_@')] = row['source']
    defs = {kind:{} for kind in ('native','canonical')}
    pointer_targets={kind:{} for kind in ('native','canonical')}
    for u in units:
        pointer_targets[u['kind']].update(u.get('pointer_targets',{}))
        for name,d in u.get('definitions',{}).items():
            if not d['static']: defs[u['kind']][name] = dict(source=u['source'],**d)
    findings=[]; asm_calls=[]; indirect=[]; indirect_findings=[]; prototypes=defaultdict(list)
    for u in units:
        if 'error' in u: continue
        for name,t in u['declarations'].items(): prototypes[(u['kind'],name)].append((u['source'],t))
        for c in u['calls']:
            d=u['definitions'].get(c['callee']) or defs[u['kind']].get(c['callee'])
            categories=[]
            if d:
                if c['declared_return'] != d['return_type']: categories.append('return-type-mismatch')
                if d['return_type'] != 'void' and (d['fallthrough'] or d['bare_return']): categories.append('unspecified-return-path')
                if c['callee'] in u['implicit_int']: categories.append('implicit-int')
            elif c['callee'] in asm:
                asm_calls.append(dict(kind=u['kind'],source=u['source'],asm_source=asm[c['callee']],**c))
            if categories: findings.append(dict(kind=u['kind'],source=u['source'],compiled_native=u['compiled_native'],categories=categories,definition=dict(source=u['source'],**d) if 'source' not in d else d,**c))
        for c in u['indirect']:
            row=dict(kind=u['kind'],source=u['source'],**c)
            candidates=pointer_targets[u['kind']].get(c.get('pointer_name'),[])
            if candidates:
                row['finite_targets']=candidates
                row['target_definitions']={n:defs[u['kind']].get(n) for n in candidates}
                for name in set(candidates):
                    d=defs[u['kind']].get(name)
                    if d is None: continue
                    categories=[]
                    if row['declared_return']!=d['return_type']: categories.append('return-type-mismatch')
                    if d['return_type']!='void' and (d['fallthrough'] or d['bare_return']): categories.append('unspecified-return-path')
                    if categories:
                        indirect_findings.append(dict(kind=u['kind'],source=u['source'],compiled_native=u['compiled_native'],
                            categories=categories,definition=d,callee=name,via_pointer=c.get('pointer_name'),
                            caller=c['caller'],line=c['line'],expression=c['expression'],declared_return=c['declared_return']))
            indirect.append(row)
    mismatches=[dict(kind=k[0],callee=k[1],declarations=v) for k,v in prototypes.items() if len({t for _,t in v})>1]
    result=dict(schema='consumed-register-return-census-v1',frontend='pycparser '+pycparser.__version__+' / GCC preprocessing',
        counts=dict(units=len(units),parsed=sum('error' not in u for u in units),
                    consumed_direct_calls=sum(len(u.get('calls',[])) for u in units),
                    findings=len(findings),asm_consumed_calls=len(asm_calls),indirect_calls=len(indirect)),
        translation_units=[{k:u[k] for k in ('source','kind','sha256','compiled_native')} for u in units if 'error' not in u],
        failures=[u for u in units if 'error' in u],findings=findings,
        asm_consumed_calls=asm_calls,indirect_calls=indirect,indirect_findings=indirect_findings,prototype_mismatches=mismatches,
        nonvoid_unspecified_definitions=[dict(kind=u['kind'],source=u['source'],name=n,**d) for u in units for n,d in u.get('definitions',{}).items() if d['return_type']!='void' and (d['fallthrough'] or d['bare_return'])],
        implicit_int=[dict(kind=u['kind'],source=u['source'],names=u.get('implicit_int',[])) for u in units if u.get('implicit_int')])
    result['unspecified_native_returns']=unspecified_native(result)
    (out/'census.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['counts'])); print(json.dumps(result['failures'],indent=2))
    return result

def unspecified_native(result):
    return [r for r in result['findings']+result.get('indirect_findings',[]) if r['kind']=='native' and r.get('compiled_native',True)
            and (r['definition']['return_type']=='void' or 'unspecified-return-path' in r['categories'] or 'implicit-int' in r['categories'])]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build',type=Path,required=True); ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--project',type=Path,default=ROOT); ap.add_argument('--cc',default='C:/msys64/mingw64/bin/gcc.exe')
    ap.add_argument('--verify',action='store_true',help='Fail if any compiled consumed void/implicit/missing result remains unspecified')
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    result=scan(a.project.resolve(),a.build.resolve(),a.out.resolve(),a.cc)
    return int(bool(result['failures']) or a.verify and bool(result['unspecified_native_returns']))

if __name__=='__main__': raise SystemExit(main())
