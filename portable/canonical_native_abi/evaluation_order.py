"""C sequencing census shared by the object evidence collector and frontend.

Calls are effectful unless explicitly proved pure. Function entry follows its
argument evaluations; comma, short circuit, conditional arms and sizeof are
sequence boundaries, not additional unsequenced operand pairs.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
from pycparser import c_ast as C, c_generator

INCREMENTS={'++','--','p++','p--'}
GEN=c_generator.CGenerator()
ROOT=Path(__file__).resolve().parents[2]
CONTRACT_PATH=ROOT/'evidence/canonical/native-evaluation-order/contracts.json'
# Neither is a canonical game call. offsetof is an unevaluated parser descriptor.
# song_span validates and returns an address without writing on its valid domain;
# failure terminates the process (which has no subsequent C evaluation).
NATIVE_READ_ONLY={'__simant_parse_only_offsetof','dos_audio_song_span'}


def effects(n):
    if n is None or isinstance(n,C.UnaryOp) and n.op=='sizeof':return []
    result=[]
    for _,child in n.children():result.extend(effects(child))
    if (isinstance(n,C.FuncCall) and not (isinstance(n.name,C.ID) and n.name.name in NATIVE_READ_ONLY)
        or isinstance(n,C.Assignment) or isinstance(n,C.UnaryOp) and n.op in INCREMENTS):
        result.append(n)
    return result


def operands(n):
    if isinstance(n,C.BinaryOp) and n.op not in {'&&','||'}:
        return 'binary:'+n.op,[n.left,n.right]
    if isinstance(n,C.FuncCall):return 'arguments',[n.name]+(n.args.exprs if n.args else [])
    if isinstance(n,C.Assignment):return 'assignment',[n.lvalue,n.rvalue]
    if isinstance(n,C.ArrayRef):return 'subscript',[n.name,n.subscript]
    if isinstance(n,C.InitList):return 'initializer',n.exprs
    return None,[]


def census(tree,active=lambda n:True):
    rows=[];function=None;occurrences=Counter()
    def walk(n):
        nonlocal function
        if n is None or isinstance(n,C.UnaryOp) and n.op=='sizeof':return
        previous=function
        if isinstance(n,C.FuncDef):function=n.decl.name
        kind,parts=operands(n)
        effectful=[i for i,p in enumerate(parts) if effects(p)]
        if active(n) and len(effectful)>1:
            expression=GEN.visit(n);key=(function,kind,expression)
            occurrences[key]+=1
            rows.append(dict(function=function,kind=kind,expression=expression,
                occurrence=occurrences[key],line=n.coord.line if n.coord else None,
                operands=effectful,effects=[[GEN.visit(e) for e in effects(p)] for p in parts],_node=n,_parts=parts))
        for _,child in n.children():walk(child)
        function=previous
    walk(tree)
    return rows


def serializable(rows):return [{k:v for k,v in r.items() if not k.startswith('_')} for r in rows]


def regions(rows):
    """Maximal overlapping sites share one schedule, including nested stores."""
    def nodes(n):
        yield n
        for _,child in n.children():yield from nodes(child)
    descendants={id(r['_node']):{id(n) for n in nodes(r['_node']) if n is not r['_node']} for r in rows}
    return [r for r in rows if not any(id(r['_node']) in d for d in descendants.values())]


def bind(tree,analysis,canonical_source,enabled=True):
    rows=census(tree,analysis.active)
    if canonical_source is None:
        # Standalone integer probes have no game/module object contract.
        return {},dict(sites=serializable(rows),status='PROBE_WITHOUT_CANONICAL_IDENTITY')
    contracts=json.loads(CONTRACT_PATH.read_text())
    expected=[r for r in contracts['sites'] if r['source']==canonical_source]
    observed=serializable(rows)
    keys=('function','kind','expression','occurrence','effects','operands')
    def identity(r):return {k:r[k] for k in keys}
    if [identity(r) for r in observed]!=[identity(r) for r in expected]:
        raise ValueError('uncovered unsequenced evaluation site or census drift: '+canonical_source)
    selected=[p for p in contracts['regions'] if p['source']==canonical_source]
    if selected and hashlib.sha256((ROOT/canonical_source).read_bytes()).hexdigest()!=selected[0]['source_sha256']:
        raise ValueError('evaluation-order canonical source changed: '+canonical_source)
    roots=regions(rows)
    if len(roots)!=len(selected):raise ValueError('evaluation-order region drift: '+canonical_source)
    plans={};receipts=[]
    for root,plan in zip(roots,selected):
        nodes=effects(root['_node'])
        if [GEN.visit(n) for n in nodes]!=plan['events']:
            raise ValueError('evaluation-order event drift: '+canonical_source)
        if sorted(plan['order'])!=list(range(len(nodes))):raise ValueError('invalid evaluation schedule')
        for n,label in zip(nodes,plan['types']):
            t=analysis.info[id(n)][0]
            if t.label()!=label or t.kind not in {'int','pointer','void','float'}:
                raise ValueError('evaluation-order event type drift: '+GEN.visit(n))
        if enabled:plans[id(root['_node'])]=(plan,nodes)
        contained={id(n) for n in analysis.nodes(root['_node'])}
        for site,record in zip(rows,observed):
            if id(site['_node']) in contained:
                record.update(region=plan['id'],reason='Unsequenced peers use the containing MSC instruction schedule, including stores interleaved across operands.')
                integer_record=analysis.record_nodes.get(id(site['_node']))
                if integer_record is not None:
                    integer_record['evaluation_order_region']=plan['id']
                    integer_record['evaluation_order_reason']=record['reason']
        receipts.append(dict(id=plan['id'],function=root['function'],expression=root['expression'],
            status='SEQUENCED' if enabled else 'DISABLED_NEGATIVE_CONTROL',
            events=plan['events'],order=plan['order'],types=plan['types'],
            instruction_evidence=plan['instructions'],
            reason='MSC object instruction/fixup schedule; typed effect results evaluated once before combination. Postincrement values can be captured before their deferred stores.'))
    return plans,dict(status='COVERED' if enabled else 'DISABLED_NEGATIVE_CONTROL',
                      sites=observed,regions=receipts,counts=dict(Counter(r['kind'] for r in rows)))
