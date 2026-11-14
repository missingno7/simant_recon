"""Conservative automatic-storage read/escape census.

Direct object stores are tracked by subobject (including symbolic array indexes).
An uninitialised local-address exposure is retained for interprocedural review.
A short list of source-reviewed output summaries establishes complete writes
(or writes only on success). Other calls, range/alias and relational uncertainty
remain candidates; this is deliberately not an absence-of-UB certificate.
"""
from collections import Counter
from pycparser import c_ast as C, c_generator
GEN=c_generator.CGenerator()
# Complete object outputs, checked against the source-backed summary receipts.
OUTPUTS={'win_GetObjRect':[1],'win_GetObjSize':[1],
         'win_get_obj_layout_rect':[1],'gr_BitMapSize':[0],'GetMousePos':[0]}
SUCCESS_OUTPUTS={'win_GetEvent':[0],'GetAntIndex':[2,3,4,5,6]}


def nodes(n):
    if n is not None:
        yield n
        for _,c in n.children():yield from nodes(c)

def census(tree,active=lambda n:True):
    rows=[]; declarations=[]
    typedefs={n.name:n.type for n in tree.ext if isinstance(n,C.Typedef)}
    structs={(type(n),n.name):n for n in nodes(tree) if isinstance(n,(C.Struct,C.Union)) and n.name and n.decls}
    def resolve(t):
        seen=set()
        while True:
            if isinstance(t,C.TypeDecl):t=t.type
            elif isinstance(t,C.IdentifierType) and len(t.names)==1 and t.names[0] in typedefs and t.names[0] not in seen:
                seen.add(t.names[0]);t=typedefs[t.names[0]]
            elif isinstance(t,(C.Struct,C.Union)) and not t.decls and (type(t),t.name) in structs:t=structs[type(t),t.name]
            else:return t
    for fn in tree.ext:
        if not isinstance(fn,C.FuncDef) or not active(fn):continue
        local={}; emitted=set()
        counts=Counter()
        def scope_walk(n,env):
            if n is None:return
            if isinstance(n,C.Compound):
                env=dict(env)
                for child in n.block_items or []:scope_walk(child,env)
                return
            if isinstance(n,C.Decl):
                if n.name and not isinstance(n.type,C.FuncDecl) and not set(n.storage)&{'static','extern','typedef'}:
                    old=n.name;counts[old]+=1;new=old if counts[old]==1 else old+'__scope'+str(counts[old]);env[old]=new;n.name=new
                    # TypeDecl is reached before the terminal IdentifierType.
                    for t in nodes(n.type):
                        if isinstance(t,C.TypeDecl):t.declname=new;break
                    scope_walk(n.init,env)
                return
            if isinstance(n,C.ID):
                if n.name in env:n.name=env[n.name]
                return
            if isinstance(n,C.StructRef):scope_walk(n.name,env);return
            for _,child in n.children():scope_walk(child,env)
        scope_walk(fn.body,{})
        def local_nodes(n):
            if n is None:return
            yield n
            if isinstance(n,C.Decl):return
            for _,child in n.children():yield from local_nodes(child)
        for n in local_nodes(fn.body):
            if isinstance(n,C.Decl) and n.name and not isinstance(n.type,C.FuncDecl) and not set(n.storage)&{'static','extern','typedef'}:
                if n.name in local:raise ValueError('shadowed local requires scoped census: '+fn.decl.name+'/'+n.name)
                local[n.name]=n
                declarations.append(dict(function=fn.decl.name,object=n.name,declaration=GEN.visit(n),line=n.coord.line))
        def path(n):
            if isinstance(n,C.ID) and n.name in local:return n.name
            if isinstance(n,C.StructRef) and n.type=='.':
                p=path(n.name);return p+'.'+n.field.name if p else None
            if isinstance(n,C.ArrayRef):
                p=path(n.name)
                # A pointer's pointee isn't an automatic subobject.
                if p and not isinstance(resolve(local[p.split('[')[0].split('.')[0]].type),C.PtrDecl):return p+'['+GEN.visit(n.subscript)+']'
            return None
        def full(p,state):
            if p in state or any(p.startswith(q+'.') or p.startswith(q+'[') for q in state):return True
            if p in local:
                t=resolve(local[p].type)
                if isinstance(t,C.Struct) and t.decls:return all(p+'.'+d.name in state for d in t.decls)
                if isinstance(t,C.Union) and t.decls:return any(p+'.'+d.name in state for d in t.decls)
                if isinstance(t,C.ArrayDecl) and isinstance(t.dim,C.Constant):
                    try:count=int(t.dim.value,0)
                    except ValueError:return False
                    return count<=256 and all(p+'['+str(i)+']' in state for i in range(count))
            return False
        def emit(n,p,kind,state,context=None):
            if p is None or full(p,state):return
            expr=GEN.visit(context or n);key=(p,kind,expr)
            if key in emitted:return
            emitted.add(key)
            rows.append(dict(function=fn.decl.name,object=p,kind=kind,expression=expr,line=n.coord.line if n.coord else None))
        def address(n,state):
            if isinstance(n,C.ArrayRef):
                if path(n) is None:read(n.name,state)
                else:address(n.name,state)
                read(n.subscript,state)
            elif isinstance(n,C.StructRef):
                if n.type=='->':read(n.name,state)
                else:address(n.name,state)
            elif isinstance(n,C.UnaryOp) and n.op=='*':read(n.expr,state)
        def output_paths(call,table):
            if not isinstance(call,C.FuncCall) or not isinstance(call.name,C.ID):return []
            result=[]
            for i in table.get(call.name.name,[]):
                a=call.args.exprs[i]
                while isinstance(a,C.Cast):a=a.expr
                if isinstance(a,C.UnaryOp) and a.op=='&':
                    p=path(a.expr)
                    if p:
                        result.append(p)
                        # Point output through Event.h also writes its adjacent v.
                        if call.name.name=='GetMousePos' and p.endswith('.h'):result.append(p[:-1]+'v')
            return result
        def refine(n,state,truth):
            if n is None:return
            # These operands are evaluated on either edge. The true && / false
            # || edge additionally proves evaluation of the conditional operand.
            def stores(x):
                if x is None or isinstance(x,C.UnaryOp) and x.op=='sizeof':return
                if isinstance(x,(C.TernaryOp,C.FuncCall)):return
                if isinstance(x,C.BinaryOp) and x.op in ('&&','||'):stores(x.left);return
                if isinstance(x,C.Assignment):
                    p=path(x.lvalue)
                    if p:state.add(p)
                for _,c in x.children():stores(c)
            stores(n)
            if isinstance(n,C.UnaryOp) and n.op=='!':return refine(n.expr,state,not truth)
            if isinstance(n,C.FuncCall):
                if truth:state.update(output_paths(n,SUCCESS_OUTPUTS))
            elif isinstance(n,C.BinaryOp):
                if n.op=='&&' and truth:refine(n.left,state,True);refine(n.right,state,True)
                elif n.op=='||' and not truth:refine(n.left,state,False);refine(n.right,state,False)
                elif isinstance(n.right,C.Constant) and n.right.value=='0' and n.op in ('==','!='):
                    refine(n.left,state,truth==(n.op=='!='))
        def read(n,state,context=None):
            if n is None:return
            if isinstance(n,C.UnaryOp) and n.op=='sizeof':return
            if isinstance(n,C.Assignment):
                address(n.lvalue,state)
                if n.op!='=':read(n.lvalue,state)
                read(n.rvalue,state)
                p=path(n.lvalue)
                if p:
                    # A symbolic element fact is valid only until an index changes.
                    if isinstance(n.lvalue,C.ID):
                        import re
                        state.difference_update(q for q in list(state) if '[' in q and re.search(r'\b'+re.escape(p)+r'\b',q[q.index('['):]))
                    state.add(p)
                return
            if isinstance(n,C.UnaryOp) and n.op=='&':
                address(n.expr,state);emit(n,path(n.expr),'address-exposure',state,context);return
            if isinstance(n,C.UnaryOp) and n.op in ('++','--','p++','p--'):
                read(n.expr,state);p=path(n.expr)
                if p:
                    import re
                    state.difference_update(q for q in list(state) if '[' in q and re.search(r'\b'+re.escape(p)+r'\b',q[q.index('['):]))
                    state.add(p)
                return
            if isinstance(n,C.FuncCall):
                read(n.name,state)
                for a in n.args.exprs if n.args else []:read(a,state,n)
                state.update(output_paths(n,OUTPUTS))
                return
            if isinstance(n,C.BinaryOp) and n.op in ('&&','||'):
                read(n.left,state);other=set(state);refine(n.left,other,n.op=='&&');read(n.right,other);state.intersection_update(other);return
            if isinstance(n,C.TernaryOp):
                read(n.cond,state);a=set(state);b=set(state);refine(n.cond,a,True);refine(n.cond,b,False);read(n.iftrue,a);read(n.iffalse,b);state.update(a&b);return
            p=path(n)
            if p:
                address(n,state)
                decl=local[p.split('[')[0].split('.')[0]]
                kind='array-decay' if isinstance(n,C.ID) and isinstance(decl.type,C.ArrayDecl) else 'read'
                emit(n,p,kind,state,context);return
            if isinstance(n,C.StructRef):read(n.name,state,context);return
            for _,c in n.children():read(c,state,context)
        # Build explicit flow edges so labels, switch fallthrough and loop exits
        # participate in the same must-initialisation fixed point.
        graph=[];labels={};gotos=[]
        def node(expr=None):
            graph.append([expr,[]]);return len(graph)-1
        def edge(a,b,truth=None):
            if b is not None:graph[a][1].append((b,truth))
        def build(n,after,break_to=None,continue_to=None,cases=None):
            if n is None:return after
            if isinstance(n,C.Compound):
                for child in reversed(n.block_items or []):after=build(child,after,break_to,continue_to,cases)
                return after
            if isinstance(n,C.If):
                at=node(n.cond);edge(at,build(n.iftrue,after,break_to,continue_to,cases),True);edge(at,build(n.iffalse,after,break_to,continue_to,cases),False);return at
            if isinstance(n,C.For):
                cond=node(n.cond);step=node(n.next);edge(step,cond)
                body=build(n.stmt,step,after,step,cases);edge(cond,body,True)
                if n.cond is not None:edge(cond,after,False)
                return build(n.init,cond,break_to,continue_to,cases)
            if isinstance(n,(C.While,C.DoWhile)):
                cond=node(n.cond);body=build(n.stmt,cond,after,cond,cases);edge(cond,body,True);edge(cond,after,False)
                return body if isinstance(n,C.DoWhile) else cond
            if isinstance(n,C.Switch):
                branches=[];build(n.stmt,after,after,continue_to,branches);at=node(n.cond)
                for target,_ in branches:edge(at,target)
                if not any(default for _,default in branches):edge(at,after)
                return at
            if isinstance(n,(C.Case,C.Default)):
                for child in reversed(n.stmts or []):after=build(child,after,break_to,continue_to,cases)
                cases.append((after,isinstance(n,C.Default)));return after
            if isinstance(n,C.Label):
                at=node();labels[n.name]=at;edge(at,build(n.stmt,after,break_to,continue_to,cases));return at
            if isinstance(n,C.Goto):
                at=node();gotos.append((at,n.name));return at
            if isinstance(n,C.Break):return break_to
            if isinstance(n,C.Continue):return continue_to
            if isinstance(n,C.Return):return node(n.expr)
            at=node(n);edge(at,after);return at
        final=node();entry=build(fn.body,final)
        for at,label in gotos:edge(at,labels[label])
        inputs={entry:set()};pending=[entry];collect=False
        def transfer(n,state):
            if isinstance(n,C.Decl):
                if n.init:read(n.init,state);state.add(n.name)
            elif isinstance(n,C.DeclList):
                for d in n.decls:transfer(d,state)
            else:read(n,state)
        # Suppress diagnostics until all reachable incoming states stabilise.
        real_emit=emit
        def emit(*args,**kwargs):
            if collect:real_emit(*args,**kwargs)
        while pending:
            at=pending.pop();state=set(inputs[at]);expr,edges=graph[at];transfer(expr,state)
            for target,truth in edges:
                outgoing=set(state)
                if truth is not None:refine(expr,outgoing,truth)
                old=inputs.get(target);new=outgoing if old is None else old&outgoing
                if old is None or new!=old:inputs[target]=new;pending.append(target)
        collect=True
        for at,state in sorted(inputs.items()):transfer(graph[at][0],set(state))
    return rows,declarations

def identity(row):return {k:row[k] for k in ('source','function','object','kind','expression') if k in row}

def verify(rows,expected):
    if [identity(r) for r in rows]!=[identity(r) for r in expected]:
        raise ValueError('unclassified automatic-storage read/escape or census drift')
    if any(not r.get('classification') or not r.get('reason') for r in expected):
        raise ValueError('automatic-storage site lacks a classification/reason')


def adapt_reference_residue(source,canonical_source,enabled=True):
    """Make the reference DOS automatic-storage input explicit in native C."""
    if canonical_source!='src/startup/main.c':return source,None
    from pathlib import Path
    import hashlib,json
    root=Path(__file__).resolve().parents[2]
    evidence=root/'evidence/canonical/uninitialised-locals/stamp-origin.json'
    digest=hashlib.sha256(evidence.read_bytes()).hexdigest()
    if digest!='05ee29c6cedf95acddc4a22cce6c8fbc304a26a324f54fa2a915005359febd63':
        raise ValueError('uninitialised stamp evidence changed; review reference environment')
    contract=json.loads(evidence.read_text())
    if hashlib.sha256((root/canonical_source).read_bytes()).hexdigest()!=contract['source_sha256']:
        raise ValueError('uninitialised stamp canonical source drift')
    anchor='int32_t stamp;'
    if source.count(anchor)!=1 or source.count('WaitedEnough(&stamp, 0x48)')!=1:
        raise ValueError('uninitialised stamp conversion anchor drift')
    if enabled:source=source.replace(anchor,'int32_t stamp = 2145517568L; /* Reference DOS CRT/DOS register-save residue; see receipt. */')
    return source,dict(status='EXPLICIT_REFERENCE_INPUT' if enabled else 'DISABLED_NEGATIVE_CONTROL',
        function='main',object='stamp',reference_value=contract['reference_value'],
        evidence='evidence/canonical/uninitialised-locals/stamp-origin.json',evidence_sha256=digest,
        canonical_source_sha256=contract['source_sha256'],
        reason='Final CRT INT 21h saves BX=0/CX=7FE2h in future BP-0Ah. CX depends on the reference DOS environment scan; native stack residue is not an input contract.')
