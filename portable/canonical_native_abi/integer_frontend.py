"""Declaration-driven MSC16/native expression census and mechanical lowering.

GCC expands macros; pycparser parses the resulting C. Only canonical-source
top-level nodes are regenerated; included native declarations remain includes.
Unknown types and machine-dependent domains are explicitly reported, never
silently classified equal. This module contains no game/module selectors.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import ast
import hashlib
import json
import re
import subprocess
import sys
import math

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'build/deps/pycparser'))
import pycparser
from pycparser import c_ast as C, c_parser, c_generator


def literal_type(text):
    """C90 MSC16 literal candidate sequence; char constants handled separately."""
    m=re.fullmatch(r'(0[xX][0-9a-fA-F]+|[0-9]+)([uUlL]*)',text)
    if not m:return None,None
    number,suffix=m.groups();suffix=suffix.lower()
    if suffix not in {'','u','l','ul','lu'}:return None,None
    try:
        base=16 if number.lower().startswith('0x') else 8 if len(number)>1 and number[0]=='0' else 10
        value=int(number,base)
    except ValueError:return None,None
    if value>0xffffffff:return None,None
    if 'l' in suffix:return ('u32' if 'u' in suffix or value>0x7fffffff else 's32'),value
    if 'u' in suffix:return ('u16' if value<=0xffff else 'u32'),value
    if value<=0x7fff:return 's16',value
    if base!=10 and value<=0xffff:return 'u16',value
    return ('s32' if value<=0x7fffffff else 'u32'),value


@dataclass(frozen=True)
class Type:
    kind: str
    bits: int = 0
    unsigned: bool = False
    rank: int = 0
    child: object = None
    name: str = ''
    count: int | None = None
    params: tuple = ()

    def label(self):
        if self.kind == 'int':
            return ('u' if self.unsigned else 's') + str(self.bits)
        return self.kind + (':' + self.name if self.name else '')

    def bounds(self):
        if self.kind != 'int':
            return None
        return (0, (1 << self.bits) - 1) if self.unsigned else (-(1 << (self.bits-1)), (1 << (self.bits-1))-1)


UNKNOWN = Type('unknown')
S8, U8 = Type('int', 8, False, 0), Type('int', 8, True, 0)
S16, U16 = Type('int', 16, False, 1), Type('int', 16, True, 1)
S32, U32 = Type('int', 32, False, 2), Type('int', 32, True, 2)
NINT = Type('int', 32, False, 1)
NUINT = Type('int', 32, True, 1)
BOOL = (S16, NINT)
FIXED = {'int8_t': S8, 'uint8_t': U8, 'int16_t': S16,
         'uint16_t': U16, 'int32_t': S32, 'uint32_t': U32,
         'int64_t': Type('int',64,False,3), 'uint64_t': Type('int',64,True,3)}


def promote(t, native=False):
    if t.kind != 'int':
        return t
    width = 32 if native else 16
    if t.bits < width:
        return NINT if native else S16
    return t


def usual(a, b, native=False):
    a, b = promote(a, native), promote(b, native)
    if a.kind == 'float' or b.kind == 'float':
        return Type('float', max(a.bits,b.bits))
    if a.kind != 'int' or b.kind != 'int':
        return UNKNOWN
    if a.unsigned == b.unsigned:
        return max((a,b), key=lambda t: (t.rank,t.bits))
    u, s = (a,b) if a.unsigned else (b,a)
    if u.rank >= s.rank:
        return u
    if s.bits > u.bits:
        return s
    return Type('int',s.bits,True,s.rank)


def cast_name(t):
    return ('uint' if t.unsigned else 'int') + str(t.bits) + '_t'


def narrow(value, t):
    if t.kind != 'int':
        return value
    value %= 1 << t.bits
    return value if t.unsigned or value < (1 << (t.bits-1)) else value - (1 << t.bits)


class Analyzer:
    def __init__(self, filename):
        self.filename = str(filename).replace('\\','/')
        self.scopes = [{}]
        self.ranges = [{}]
        self.address_taken = set()
        self.flow_enabled = True
        self.switch_writes = []
        self.typedef_scopes = [{}]
        self.tag_scopes = [{}]
        self.structs = {}
        self.info = {}
        self.actions = {}
        self.records = []
        self.record_nodes = {}
        self.unresolved = set()
        self.function = None

    def active(self, node):
        return node.coord is not None and node.coord.file.replace('\\','/') == self.filename

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return (UNKNOWN,UNKNOWN)

    def push(self):
        self.scopes.append({});self.ranges.append({})
        self.typedef_scopes.append({});self.tag_scopes.append({})

    def pop(self):
        self.scopes.pop();self.ranges.pop()
        self.typedef_scopes.pop();self.tag_scopes.pop()

    def bound(self,name):
        for index in range(len(self.scopes)-1,-1,-1):
            if name in self.scopes[index]:
                d=self.scopes[index][name][0]
                return self.ranges[index].get(name,d.bounds())
        return None

    def set_bound(self,name,bound):
        if not self.flow_enabled:return
        for index in range(len(self.scopes)-1,0,-1):
            if name in self.scopes[index]:
                t=self.scopes[index][name][0]
                if name in self.address_taken or t.kind!='int':return
                low,high=t.bounds()
                if bound and bound[0]==bound[1]:bound=(narrow(bound[0],t),)*2
                elif not bound or not low<=bound[0]<=bound[1]<=high:bound=t.bounds()
                self.ranges[index][name]=bound
                return

    def nodes(self,n):
        if n is not None:
            yield n
            for _,child in n.children():yield from self.nodes(child)

    def writes(self,n):
        names=set()
        for node in self.nodes(n):
            if isinstance(node,C.Assignment) and isinstance(node.lvalue,C.ID):names.add(node.lvalue.name)
            if isinstance(node,C.UnaryOp) and node.op in {'++','--','p++','p--'} and isinstance(node.expr,C.ID):names.add(node.expr.name)
        return names

    def forget(self,names):
        for name in names:self.set_bound(name,self.lookup(name)[0].bounds())

    def polynomial_coefficients(self,n):
        """Conservative integer numerator factors; no symbolic game identities."""
        bound=self.info.get(id(n),(None,None,None))[2]
        if bound and bound[0]==bound[1]:return [bound[0]]
        if isinstance(n,C.BinaryOp) and n.op in {'+','-'}:
            return self.polynomial_coefficients(n.left)+self.polynomial_coefficients(n.right)
        if isinstance(n,C.BinaryOp) and n.op=='*':
            left=self.info[id(n.left)][2];right=self.info[id(n.right)][2]
            if right and right[0]==right[1]:return [c*right[0] for c in self.polynomial_coefficients(n.left)]
            if left and left[0]==left[1]:return [c*left[0] for c in self.polynomial_coefficients(n.right)]
        return [1]

    def withhold(self,n):
        for child in self.nodes(n):
            if id(child) in self.actions:
                self.actions.pop(id(child))
                self.unresolved.add(id(child))
                row=self.record_nodes.get(id(child))
                if row:
                    row['status']='UNRESOLVED'
                    row['categories'].append('msc-algebra-parent')
                    row['reason']='Lowering withheld with a containing MSC constant-algebra domain; no intermediate wrap is forced across target contraction.'

    def snapshot(self):return [dict(r) for r in self.ranges]

    def merge_ranges(self,a,b):
        self.ranges=[{} for _ in self.scopes]
        for i,scope in enumerate(self.scopes):
            for name,(t,_) in scope.items():
                x=a[i].get(name,t.bounds());y=b[i].get(name,t.bounds())
                if x and y:self.ranges[i][name]=(min(x[0],y[0]),max(x[1],y[1]))

    def refine(self,n,truth=True):
        if isinstance(n,C.UnaryOp) and n.op=='!':return self.refine(n.expr,not truth)
        if isinstance(n,C.BinaryOp) and ((n.op=='&&' and truth) or (n.op=='||' and not truth)):
            self.refine(n.left,truth);self.refine(n.right,truth);return
        if not isinstance(n,C.BinaryOp) or n.op not in {'<','<=','>','>=','==','!='}:return
        if id(n) in self.unresolved or not isinstance(n.left,C.ID):return
        name=n.left.name
        a,_,ab=self.info[id(n.left)];b,_,bb=self.info[id(n.right)]
        if not ab or not bb:return
        common=usual(a,b)
        if common.kind!='int' or not common.bounds()[0]<=ab[0]<=ab[1]<=common.bounds()[1]:return
        op=n.op if truth else {'<':'>=','<=':'>','>':'<=','>=':'<','==':'!=','!=':'=='}[n.op]
        low,high=self.bound(name) or ab
        if op=='<':high=min(high,bb[1]-1)
        elif op=='<=':high=min(high,bb[1])
        elif op=='>':low=max(low,bb[0]+1)
        elif op=='>=':low=max(low,bb[0])
        elif op=='==' and bb[0]==bb[1]:low,high=bb
        if low<=high:self.set_bound(name,(low,high))

    def type(self, n, native=False):
        if n is None:
            return UNKNOWN
        if isinstance(n, (C.Decl,C.Typename,C.Typedef,C.TypeDecl)):
            return self.type(n.type,native)
        if isinstance(n,C.IdentifierType):
            names = n.names
            name = ' '.join(names)
            if name in FIXED:
                return FIXED[name]
            if name == 'size_t':
                return Type('int',64,True,3) if native else U16
            if name == 'ptrdiff_t':
                return Type('int',64,False,3) if native else S16
            for scope in reversed(self.typedef_scopes):
                if name in scope:return scope[name][int(native)]
            if 'void' in names:
                return Type('void')
            if 'double' in names or 'float' in names:
                return Type('float',64 if 'double' in names else 32)
            if 'char' in names:
                return U8 if 'unsigned' in names else S8
            unsigned = 'unsigned' in names
            if names == ['_Bool']:
                return U8
            if 'short' in names:
                return U16 if unsigned else S16
            if 'long' in names:
                bits = 64 if names.count('long') == 2 else 32
                return Type('int',bits,unsigned,3 if bits == 64 else 2)
            if set(names) <= {'int','signed','unsigned'}:
                return (NUINT if unsigned else NINT) if native else (U16 if unsigned else S16)
            return UNKNOWN
        if isinstance(n,C.PtrDecl):
            return Type('pointer',64 if native else 32,child=self.type(n.type,native))
        if isinstance(n,C.ArrayDecl):
            count = None
            if n.dim is not None:
                self.expr(n.dim)
                r = self.info[id(n.dim)][2]
                if r and r[0] == r[1]: count = r[0]
            return Type('array',child=self.type(n.type,native),count=count)
        if isinstance(n,C.FuncDecl):
            params = tuple(self.type(p,native) if not isinstance(p,C.EllipsisParam) else Type('ellipsis')
                           for p in (n.args.params if n.args else []))
            return Type('function',child=self.type(n.type,native),params=params)
        if isinstance(n,(C.Struct,C.Union)):
            tag=(type(n).__name__,n.name)
            if n.name and n.decls is None:
                key=next((scope[tag] for scope in reversed(self.tag_scopes) if tag in scope),None)
            else:key=self.tag_scopes[-1].get(tag) if n.name else None
            if key is None:
                key=(type(n).__name__,(n.name or '')+'@'+str(n.coord))
                if n.name:self.tag_scopes[-1][tag]=key
            if n.decls is not None:
                fields={}
                for decl in n.decls:
                    pair=self.type(decl,False),self.type(decl,True)
                    if decl.name is not None:fields[decl.name]=pair
                    elif pair[0].kind=='struct':fields.update(self.structs.get(tuple(pair[0].name.split(':',1)),{}))
                self.structs[key] = fields
            return Type('struct',name=':'.join(key))
        if isinstance(n,C.Enum):
            if n.values:
                value = -1
                for e in n.values.enumerators:
                    if e.value:
                        self.expr(e.value)
                        r=self.info[id(e.value)][2]
                        value = r[0] if r and r[0]==r[1] else 0
                    else: value += 1
                    self.scopes[-1][e.name] = BOOL
            return NINT if native else S16
        return UNKNOWN

    def remember(self,n,d,nat,bound=None,categories=(),action=None,reason=None,equal=False):
        self.info[id(n)] = (d,nat,bound)
        categories=list(categories)
        open_domain=any(c.endswith('-domain') and c!='division-zero-domain' for c in categories)
        dependent=not (isinstance(n,C.UnaryOp) and n.op=='sizeof') and any(id(child) in self.unresolved for _,child in n.children())
        if open_domain or dependent:
            action=None
            equal=False
            if dependent:categories.append('unresolved-child')
            reason=('Child value/domain remains unresolved; no parent equivalence or lowering is assumed.' if dependent
                    else 'Complete operand interval admits undefined or compiler-dependent MSC behavior; retained without lowering.')
        if not self.active(n):
            if d.kind=='unknown' or nat.kind=='unknown' or open_domain or dependent:self.unresolved.add(id(n))
            return d,nat,bound
        row={'file':self.filename,'line':n.coord.line,'column':n.coord.column,
             'function':self.function,'node':type(n).__name__,
             'operator':getattr(n,'op',None),'msc16_type':d.label(),
             'native_type':nat.label(),'categories':list(categories)}
        if bound is not None: row['msc16_bound']=list(bound)
        if d.kind == 'unknown' or nat.kind == 'unknown':
            row['categories'].append('unknown-type')
            row['status']='UNRESOLVED'
            row['reason']='Declaration/operand type is not resolved; no equivalence assumed.'
        elif action:
            row['status']='LOWERED'
            row['reason']=reason or 'MSC integer promotions and usual arithmetic conversion; operation narrowed before consumer.'
            self.actions[id(n)] = action
        elif categories and not equal:
            row['status']='UNRESOLVED'
            row['reason']=reason or 'Machine/layout-dependent domain requires separate evidence.'
        else:
            row['status']='PROVEN_EQUAL'
            row['reason']=reason or 'Fixed-width leaf value or operation has identical value after usual conversions.'
        self.records.append(row)
        self.record_nodes[id(n)]=row
        if 'division-zero-domain' in categories:
            row['excluded_domain']='Division by zero is undefined in both models; this operation is lowered only for nonzero divisors. Trap identity is unclaimed.'
        if row['status']=='UNRESOLVED':self.unresolved.add(id(n))
        return d,nat,bound

    def expr(self,n):
        if n is None: return UNKNOWN,UNKNOWN,None
        if id(n) in self.info: return self.info[id(n)]
        if isinstance(n,C.ID):
            d,nat=self.lookup(n.name)
            return self.remember(n,d,nat,self.bound(n.name),reason='Declared range, refined only by nonescaping local assignments or dominating integer guards.')
        if isinstance(n,C.Constant):
            if n.type == 'string':
                return self.remember(n,Type('array',child=S8),Type('array',child=S8),reason='String byte values and signed-char build flag agree; pointer layout excluded.')
            if n.type == 'char':
                try: value=ord(ast.literal_eval(n.value))
                except Exception: value=None
                cats=() if value is not None and value < 128 else ('character-constant',)
                return self.remember(n,*BOOL,(value,value) if value is not None else None,cats)
            typ,value=literal_type(n.value)
            if typ:
                d={'s16':S16,'u16':U16,'s32':S32,'u32':U32}[typ]
                suffix=re.search('[uUlL]+$',n.value)
                s=suffix[0].lower() if suffix else ''
                decimal=not (n.value.lower().startswith('0x') or len(n.value)>1 and n.value[0]=='0')
                if 'u' in s:nat=U32 if 'l' in s else NUINT
                elif value>0x7fffffff and decimal:nat=Type('int',64,False,3)
                elif 'l' in s:nat=U32 if value>0x7fffffff else S32
                else:nat=NUINT if value>0x7fffffff else NINT
                if not s and decimal and value>0x7fffffff:
                    return self.remember(n,UNKNOWN,nat,None,('literal-typing','msc-large-decimal-domain'),
                        reason='Real MSC unsuffixed decimal above signed-long range contradicts the C90 candidate model; target literal typing remains unresolved.')
                action=('literal',d) if d.unsigned != nat.unsigned else None
                # A small literal's type width alone cannot alter its value.
                return self.remember(n,d,nat,(value,value),('literal-typing',) if d!=nat else (),action,
                                     'MSC literal candidate sequence; cast preserves signedness through parent operations.' if action else 'Literal value is representable in both selected types; parent uses independently computed MSC type.',equal=not action)
            if n.type in {'float','double','long double'}:
                t=Type('float',32 if n.type=='float' else 64)
                return self.remember(n,t,t)
            return self.remember(n,UNKNOWN,UNKNOWN,None,('literal-typing',))
        if isinstance(n,C.Cast):
            cd,cn,b=self.expr(n.expr)
            d,nat=self.type(n.to_type),self.type(n.to_type,True)
            cats=('pointer-integer-cast',) if {cd.kind,d.kind}=={'pointer','int'} else ()
            bound=d.bounds()
            if b and b[0]==b[1] and d.kind=='int': bound=(narrow(b[0],d),)*2
            elif b and d.kind=='int' and d.bounds()[0]<=b[0]<=b[1]<=d.bounds()[1]:bound=b
            return self.remember(n,d,nat,bound,cats)
        if isinstance(n,C.ArrayRef):
            d,nat,_=self.expr(n.name);self.expr(n.subscript)
            return self.remember(n,d.child or UNKNOWN,nat.child or UNKNOWN,
                                 (d.child or UNKNOWN).bounds())
        if isinstance(n,C.StructRef):
            d,nat,_=self.expr(n.name)
            if n.type=='->':d,nat=d.child or UNKNOWN,nat.child or UNKNOWN
            fields=self.structs.get(tuple(d.name.split(':',1)),{})
            dt,nt=fields.get(n.field.name,(UNKNOWN,UNKNOWN))
            return self.remember(n,dt,nt,dt.bounds())
        if isinstance(n,C.FuncCall):
            if isinstance(n.name,C.ID) and n.name.name=='__simant_parse_only_offsetof':
                result=self.remember(n,U16,Type('int',64,True,3),None,('offsetof-layout',),
                    reason='Native offsetof is preserved verbatim; DOS/native physical layout equality is unresolved.')
                if self.active(n):self.record_nodes[id(n)]['intrinsic']='offsetof'
                return result
            d,nat,_=self.expr(n.name)
            if d.kind=='pointer':d,nat=d.child or UNKNOWN,nat.child or UNKNOWN
            if n.args:
                for arg in n.args.exprs:self.expr(arg)
            dt,nt=d.child or UNKNOWN,nat.child or UNKNOWN
            action=('call',dt) if dt.kind=='int' and nt.bits>dt.bits else None
            return self.remember(n,dt,nt,dt.bounds(),('call-return-width',) if action else (),action)
        if isinstance(n,C.ExprList):
            values=[self.expr(e) for e in n.exprs]
            return self.remember(n,*values[-1])
        if isinstance(n,C.TernaryOp):
            self.expr(n.cond);a,an,ab=self.expr(n.iftrue);b,bn,bb=self.expr(n.iffalse)
            if a.kind=='int' and b.kind=='int':
                d,nat=usual(a,b),usual(an,bn,True)
                return self.remember(n,d,nat,d.bounds(),('conditional-conversion',),('conditional',d))
            if a.kind in {'pointer','array'} and b.kind=='int' and bb==(0,0):return self.remember(n,a,an)
            if b.kind in {'pointer','array'} and a.kind=='int' and ab==(0,0):return self.remember(n,b,bn)
            if a.kind=='array' and b.kind=='array' and a.child==b.child:
                return self.remember(n,Type('pointer',32,child=a.child),Type('pointer',64,child=an.child))
            return self.remember(n,a if a==b else UNKNOWN,an if an==bn else UNKNOWN)
        if isinstance(n,C.Assignment):
            a,an,ab=self.expr(n.lvalue);b,bn,bb=self.expr(n.rvalue)
            cats=[];action=None
            if n.op!='=' and a.kind=='int' and b.kind=='int':
                d=promote(a) if n.op in {'<<=','>>='} else usual(a,b)
                cats=['compound-arithmetic'];action=('compound',d)
                if not d.unsigned and n.op in {'+=','-=','*='}:cats.append('signed-overflow-domain')
                if n.op in {'<<=','>>='} and (not bb or bb[0]<0 or bb[1]>=d.bits):
                    cats.append('shift-count-domain');action=None
                if n.op in {'/=','%='} and (not bb or bb[0]<=0<=bb[1]):
                    cats.append('division-zero-domain')
                if not d.unsigned and n.op in {'/=','%='} and ab and bb and ab[0]<=d.bounds()[0]<=ab[1] and bb[0]<=-1<=bb[1]:
                    cats.append('division-overflow-domain')
                if not d.unsigned and n.op=='<<=':
                    if not ab or ab[0]<0:cats.append('shift-negative-domain')
                    if not ab or not bb or bb[1]>=d.bits or bb[0]<0 or ab[1]*(1<<bb[1])>d.bounds()[1]:cats.append('signed-overflow-domain')
                if not d.unsigned and n.op=='>>=' and ab and ab[0]<0:
                    cats.append('arithmetic-right-shift')
                # The helper evaluates the lvalue address before the RHS.
                # With an effectful address, permit this only for a constant or
                # nonescaping local scalar RHS independent of address mutations.
                effectful=any(isinstance(node,C.FuncCall) or isinstance(node,C.Assignment) or
                              isinstance(node,C.UnaryOp) and node.op in {'++','--','p++','p--'}
                              for node in self.nodes(n.lvalue))
                if effectful:
                    local_names=set().union(*(scope.keys() for scope in self.scopes[1:]))
                    safe_nodes=(C.ID,C.Constant,C.Cast,C.UnaryOp,C.BinaryOp,C.Typename,C.TypeDecl,C.IdentifierType)
                    independent=all(isinstance(node,safe_nodes) and
                                    (not isinstance(node,C.ID) or node.name in local_names and node.name not in self.address_taken and node.name not in self.writes(n.lvalue)) and
                                    (not isinstance(node,C.UnaryOp) or node.op not in {'++','--','p++','p--','*','&'})
                                    for node in self.nodes(n.rvalue))
                    if not independent:cats.append('operand-order-domain')
            return self.remember(n,a,an,a.bounds(),cats,action)
        if isinstance(n,C.UnaryOp):
            if n.op=='sizeof':
                if isinstance(n.expr,C.Typename): d,nat=self.type(n.expr),self.type(n.expr,True)
                else:d,nat,_=self.expr(n.expr)
                if d.kind in {'int','float'}:
                    action=('sizeof',d) if d.bits!=nat.bits else None
                    return self.remember(n,U16,Type('int',64,True,3),(d.bits//8,)*2,
                                         ('sizeof-scalar',) if action else (),action,
                                         reason='Scalar sizeof uses MSC operand type; expression operand stays unevaluated.')
                return self.remember(n,U16,Type('int',64,True,3),None,('sizeof-layout',))
            a,an,b=self.expr(n.expr)
            if n.op=='&':return self.remember(n,Type('pointer',32,child=a),Type('pointer',64,child=an))
            if n.op=='*':
                d,nat=a.child or UNKNOWN,an.child or UNKNOWN
                return self.remember(n,d,nat,d.bounds())
            if n.op=='!':return self.remember(n,*BOOL,(0,1),reason='Truth values agree after lowered child; C result is zero or one.')
            if n.op in {'++','--','p++','p--'}:
                cats=('pointer-arithmetic',) if a.kind=='pointer' else ()
                if a.kind=='int' and not a.unsigned:
                    step=1 if '+' in n.op else -1
                    low,high=a.bounds()
                    if not b or b[0]+step<low or b[1]+step>high:cats=('signed-overflow-domain',)
                result=b
                if b and n.op in {'++','--'}:
                    step=1 if '+' in n.op else -1;result=(b[0]+step,b[1]+step)
                    if result[0]==result[1]:result=(narrow(result[0],a),)*2
                    elif a.kind=='int' and not a.bounds()[0]<=result[0]<=result[1]<=a.bounds()[1]:result=a.bounds()
                return self.remember(n,a,an,result,cats,reason='Declared/refined lvalue interval keeps increment in range; fixed-width store/result agrees.')
            d,nat=promote(a),promote(an,True)
            action=('unary',d) if d.kind=='int' and d.bits<=32 else None
            cats=['unary-promotion'] if action else []
            if n.op=='-' and d.kind=='int' and not d.unsigned and b and b[0]<=d.bounds()[0]<=b[1]:cats.append('signed-overflow-domain')
            return self.remember(n,d,nat,d.bounds(),cats,action)
        if isinstance(n,C.BinaryOp):
            a,an,ab=self.expr(n.left);b,bn,bb=self.expr(n.right)
            if n.op in {'&&','||'}:
                return self.remember(n,*BOOL,(0,1),reason='Short-circuit operands stay in source order; boolean range is 0..1.')
            if 'pointer' in {a.kind,b.kind} or 'array' in {a.kind,b.kind}:
                if n.op in {'==','!=','<','>','<=','>='}:
                    return self.remember(n,*BOOL,(0,1),('pointer-comparison',))
                d=a if a.kind in {'pointer','array'} else b
                nt=an if an.kind in {'pointer','array'} else bn
                if n.op=='-' and a.kind in {'pointer','array'} and b.kind in {'pointer','array'}: d,nt=S16,Type('int',64,False,3)
                return self.remember(n,d,nt,None,('pointer-arithmetic',))
            d=promote(a) if n.op in {'<<','>>'} else usual(a,b)
            nat=promote(an,True) if n.op in {'<<','>>'} else usual(an,bn,True)
            if d.kind=='float':return self.remember(n,d,nat)
            if d.kind!='int':return self.remember(n,UNKNOWN,nat)
            compare=n.op in {'==','!=','<','>','<=','>='}
            cats=[];action=('binary',d)
            if compare:
                if d.unsigned!=nat.unsigned:cats.append('signed-unsigned-comparison')
                else: cats.append('comparison-conversion')
                if ab and bb:
                    low,high=d.bounds();nl,nh=nat.bounds()
                    if all(low<=bound[0]<=bound[1]<=high and nl<=bound[0]<=bound[1]<=nh for bound in (ab,bb)):
                        return self.remember(n,*BOOL,(0,1),cats,reason='Both declaration/literal intervals fit both common types; comparison order is preserved.',equal=True)
            elif n.op in {'+','-','*'}:cats.append('intermediate-'+({'+':'add','-':'subtract','*':'product'}[n.op]))
            elif n.op in {'/','%'}:
                cats.append('division-modulo')
                # MSC's constant algebra contraction can violate even unsigned
                # modulo semantics. Do not insert a wrap that was optimized out
                # by the target compiler (INT16-1 positive/negative controls).
                if bb and bb[0]==bb[1] and bb[0]>1:
                    coefficients=self.polynomial_coefficients(n.left)
                    factor=math.gcd(bb[0],*coefficients)
                    has_wrap=any(r.get('status')=='LOWERED' or 'signed-overflow-domain' in r['categories']
                                 for node in self.nodes(n.left) if (r:=self.record_nodes.get(id(node))) and isinstance(node,C.BinaryOp) and node.op in {'+','-','*'})
                    if factor>1 and has_wrap:
                        cats.append('msc-constant-algebra-domain')
                        self.withhold(n.left)
                if not bb or bb[0]<=0<=bb[1]:cats.append('division-zero-domain')
                if not d.unsigned and ab and bb and ab[0]<=d.bounds()[0]<=ab[1] and bb[0]<=-1<=bb[1]:cats.append('division-overflow-domain')
            elif n.op in {'<<','>>'}:
                cats.append('shift-promotion')
                if not bb or bb[0]<0 or bb[1]>=d.bits:
                    cats.append('shift-count-domain');action=None
                if not d.unsigned and ab and ab[0]<0:
                    cats.append('shift-negative-domain' if n.op=='<<' else 'arithmetic-right-shift')
                if not d.unsigned and n.op=='<<' and bb and ab and bb[0]>=0:
                    if bb[1]>=d.bits or ab[1]*(1<<bb[1])>d.bounds()[1]:cats.append('signed-overflow-domain')
            else:cats.append('bitwise-promotion')
            reason=None
            # This intentionally uses declaration bounds only, not guessed path facts.
            if n.op in {'+','-','*'} and ab and bb:
                pairs=[x*y for x in ab for y in bb]
                bound={'+':(ab[0]+bb[0],ab[1]+bb[1]),'-':(ab[0]-bb[1],ab[1]-bb[0]),'*':(min(pairs),max(pairs))}[n.op]
                low,high=d.bounds()
                if low<=bound[0]<=bound[1]<=high and d.unsigned==nat.unsigned:
                    return self.remember(n,d,nat,bound,reason='Declaration/literal interval arithmetic proves intermediate within MSC result range; signedness agrees.')
            result_bound=d.bounds()
            if n.op=='&' and bb and bb[0]==bb[1] and 0<=bb[0]<=d.bounds()[1]:result_bound=(0,bb[0])
            if n.op=='&' and ab and ab[0]==ab[1] and 0<=ab[0]<=d.bounds()[1]:result_bound=(0,ab[0])
            if n.op in {'+','-','*'} and not d.unsigned:cats.append('signed-overflow-domain')
            return self.remember(n,*(BOOL if compare else (d,nat)),(0,1) if compare else result_bound,cats,action,reason)
        if isinstance(n,C.InitList):
            for e in n.exprs:self.expr(e)
            return UNKNOWN,UNKNOWN,None
        if isinstance(n,C.NamedInitializer):
            for e in n.name:
                if not isinstance(e,C.ID):self.expr(e)
            return self.expr(n.expr)
        return self.remember(n,UNKNOWN,UNKNOWN,None,('unsupported-expression',))

    def walk(self,n):
        if n is None:return
        if isinstance(n,C.FileAST):
            for e in n.ext:self.walk(e)
        elif isinstance(n,C.Typedef):
            self.typedef_scopes[-1][n.name]=(self.type(n),self.type(n,True))
        elif isinstance(n,C.FuncDef):
            self.walk(n.decl)
            previous=self.function;self.function=n.decl.name
            previous_address_taken=self.address_taken
            previous_flow=self.flow_enabled
            self.flow_enabled=not any(isinstance(node,C.Goto) for node in self.nodes(n.body))
            self.address_taken={node.expr.name for node in self.nodes(n.body) if isinstance(node,C.UnaryOp) and node.op=='&' and isinstance(node.expr,C.ID)}
            self.address_taken.update(node.name for node in self.nodes(n) if isinstance(node,C.Decl) and ('volatile' in node.quals or 'static' in node.storage))
            self.push()
            for p in n.decl.type.args.params if n.decl.type.args else []:
                if isinstance(p,C.Decl):self.walk(p)
            for p in n.param_decls or []:self.walk(p)
            self.walk(n.body)
            self.pop();self.function=previous;self.address_taken=previous_address_taken;self.flow_enabled=previous_flow
        elif isinstance(n,C.Decl):
            types=self.type(n),self.type(n,True)
            if n.name:self.scopes[-1][n.name]=types
            if n.init:
                self.forget(self.writes(n.init));_,_,bound=self.expr(n.init)
                if n.name:self.set_bound(n.name,bound if id(n.init) not in self.unresolved else None)
            if n.bitsize:self.expr(n.bitsize)
        elif isinstance(n,C.Compound):
            self.push()
            for e in n.block_items or []:self.walk(e)
            self.pop()
        elif isinstance(n,C.For):
            self.push();self.walk(n.init)
            written=self.writes(n.stmt)|self.writes(n.next)|self.writes(n.cond)
            candidate=None
            start=None
            if isinstance(n.next,C.UnaryOp) and isinstance(n.next.expr,C.ID):start=self.bound(n.next.expr.name)
            # A mutable limit must use its entire loop-carried domain, rather
            # than the value stored before the first iteration.
            self.forget(written)
            if isinstance(n.next,C.UnaryOp) and n.next.op in {'++','p++'} and isinstance(n.next.expr,C.ID):
                name=n.next.expr.name
                cond=n.cond
                if start and start[0]==start[1] and isinstance(cond,C.BinaryOp) and cond.op in {'<','<='} and isinstance(cond.left,C.ID) and cond.left.name==name:
                    # The candidate limit can vary through globals/calls, but its
                    # full declared type bounds must suffice for every iteration.
                    limit=self.expr(cond.right)
                    upper=limit[2][1]-(1 if cond.op=='<' else 0) if limit[2] else None
                    low,high=self.lookup(name)[0].bounds() or (0,-1)
                    self_reference=any(isinstance(node,C.ID) and node.name==name for node in self.nodes(cond.right))
                    if upper is not None and not self_reference and id(cond.right) not in self.unresolved and start[0]<=upper and low<=start[0] and upper+1<=high and name not in self.writes(n.stmt) and name not in self.writes(n.cond) and name not in self.address_taken:
                        candidate=(name,start[0],upper)
            self.forget(written)
            if candidate:self.set_bound(candidate[0],(candidate[1],candidate[2]+1))
            self.walk(n.cond)
            if candidate:self.set_bound(candidate[0],(candidate[1],candidate[2]))
            self.walk(n.stmt);self.walk(n.next)
            self.forget(written);self.pop()
        elif isinstance(n,C.If):
            self.walk(n.cond);before=self.snapshot()
            self.refine(n.cond,True);self.walk(n.iftrue);yes=self.snapshot()
            self.ranges=[dict(r) for r in before]
            self.refine(n.cond,False);self.walk(n.iffalse);no=self.snapshot()
            self.merge_ranges(yes,no)
        elif isinstance(n,(C.While,C.DoWhile)):
            written=self.writes(n)
            self.forget(written)
            self.walk(n.cond);self.walk(n.stmt)
            self.forget(written)
        elif isinstance(n,C.Switch):
            self.walk(n.cond)
            written=self.writes(n.stmt);self.forget(written)
            self.switch_writes.append(written);self.walk(n.stmt);self.switch_writes.pop()
            self.forget(written)
        elif isinstance(n,(C.Case,C.Default)):
            if self.switch_writes:self.forget(self.switch_writes[-1])
            for _,child in n.children():self.walk(child)
        elif isinstance(n,C.ExprList):
            for expr in n.exprs:self.walk(expr)
        elif isinstance(n,(C.ID,C.Constant,C.Cast,C.ArrayRef,C.StructRef,C.FuncCall,C.ExprList,C.TernaryOp,C.Assignment,C.UnaryOp,C.BinaryOp)):
            simple=isinstance(n,C.Assignment) and n.op=='=' and isinstance(n.lvalue,C.ID)
            update=isinstance(n,C.UnaryOp) and n.op in {'++','--','p++','p--'} and isinstance(n.expr,C.ID)
            if simple:
                self.forget(self.writes(n.rvalue));self.expr(n)
                self.set_bound(n.lvalue.name,self.info[id(n.rvalue)][2] if id(n.rvalue) not in self.unresolved else None)
            elif update:
                a,_,bound=self.expr(n.expr);self.expr(n)
                step=1 if '+' in n.op else -1
                self.set_bound(n.expr.name,(bound[0]+step,bound[1]+step) if bound and id(n) not in self.unresolved else None)
            else:
                self.forget(self.writes(n));self.expr(n)
        elif isinstance(n,(C.Pragma,C.EmptyStatement,C.Break,C.Continue,C.Goto,C.StaticAssert)):
            pass
        else:
            for _,e in n.children():self.walk(e)


class Generator(c_generator.CGenerator):
    def __init__(self,analyzer,assertions):
        super().__init__();self.analysis=analyzer;self.assertions=assertions
        self.helper_name='simant_int_lvalue'
        while self.helper_name in analyzer.reserved_identifiers:
            self.helper_name+='_' 

    def visit_StaticAssert(self,n):
        if not self.analysis.active(n) or n.coord.line not in self.assertions:
            raise ValueError('Expanded layout assertion has no original native assertion to restore')
        return self.assertions[n.coord.line]+'\n'

    def cast(self,t,text):return '(('+cast_name(t)+')('+text+'))'

    def visit_Constant(self,n):
        action=self.analysis.actions.get(id(n))
        return self.cast(action[1],n.value) if action else super().visit_Constant(n)

    def visit_BinaryOp(self,n):
        action=self.analysis.actions.get(id(n))
        if not action:return super().visit_BinaryOp(n)
        d=action[1];left=self.cast(d,self.visit(n.left));right=self.cast(d,self.visit(n.right))
        if n.op in {'==','!=','<','>','<=','>='}:return '('+left+' '+n.op+' '+right+')'
        # Widen after the DOS usual conversions, perform once, narrow before
        # any consumer. int64 can hold a signed32 product; uint64 arithmetic
        # defines unsigned32 products without native signed overflow.
        wide='uint64_t' if d.unsigned else 'int64_t'
        return self.cast(d,'(('+wide+')('+left+')) '+n.op+' (('+wide+')('+right+'))')

    def visit_UnaryOp(self,n):
        action=self.analysis.actions.get(id(n))
        if not action:return super().visit_UnaryOp(n)
        d=action[1]
        if action[0]=='sizeof':return '((uint16_t)'+str(d.bits//8)+')'
        wide='uint64_t' if d.unsigned else 'int64_t'
        return self.cast(d,n.op+'(('+wide+')('+self.cast(d,self.visit(n.expr))+'))')

    def visit_FuncCall(self,n):
        if isinstance(n.name,C.ID) and n.name.name=='__simant_parse_only_offsetof':
            if not n.args or len(n.args.exprs)!=2 or not all(isinstance(arg,C.Constant) and arg.type=='string' for arg in n.args.exprs):
                raise ValueError('Malformed parse-only offsetof descriptor')
            return 'offsetof('+', '.join(ast.literal_eval(arg.value) for arg in n.args.exprs)+')'
        text=super().visit_FuncCall(n)
        action=self.analysis.actions.get(id(n))
        return self.cast(action[1],text) if action else text

    def visit_TernaryOp(self,n):
        action=self.analysis.actions.get(id(n))
        if not action:return super().visit_TernaryOp(n)
        d=action[1]
        return '('+self.visit(n.cond)+' ? '+self.cast(d,self.visit(n.iftrue))+' : '+self.cast(d,self.visit(n.iffalse))+')'

    def visit_Assignment(self,n):
        action=self.analysis.actions.get(id(n))
        if not action:return super().visit_Assignment(n)
        # GNU statement expression preserves one lvalue evaluation, including
        # volatile and side-effecting address/index producers.
        d=action[1];l=self.visit(n.lvalue);r=self.visit(n.rvalue);op=n.op[:-1]
        helper=self.helper_name
        wide='uint64_t' if d.unsigned else 'int64_t'
        value=self.cast(d,'(('+wide+')('+self.cast(d,'*'+helper)+')) '+op+' (('+wide+')('+self.cast(d,r)+'))')
        return '(__extension__ ({ __auto_type '+helper+' = &('+l+'); *'+helper+' = '+value+'; }))'


def preprocess(source, filename, cc, include_dirs):
    fake=Path(__file__).with_name('integer_fake_libc')
    command=[cc,'-E','-std=c11','-nostdinc','-D__attribute__(x)=','-D__extension__=',
             '-I',str(fake)]
    for directory in include_dirs:command+=['-I',str(directory)]
    command+=['-x','c','-']
    escaped=str(filename).replace('\\','/').replace('"','\\"')
    run=subprocess.run(command,input='#line 1 "'+escaped+'"\n'+source,capture_output=True,text=True,timeout=30)
    if run.returncode:raise ValueError(run.stderr)
    return run.stdout,command


def convert(source, filename, cc, include_dirs, lower=True):
    preprocessed,command=preprocess(source,filename,cc,include_dirs)
    tree=c_parser.CParser().parse(preprocessed,filename=str(filename))
    analysis=Analyzer(filename);analysis.walk(tree)
    analysis.reserved_identifiers=set(re.findall(r'\b[A-Za-z_]\w*\b',source+preprocessed))
    includes='\n'.join(re.findall(r'^\s*#\s*include[^\n]*',source,re.M))+'\n'
    # Macros have already expanded in the AST. Real headers retain their native
    # types, assertions and layout macros; fake libc is parse-only.
    output=includes
    original_assertions={source.count('\n',0,m.start())+1:m[0]
                         for m in re.finditer(r'_Static_assert\s*\([^;]*;',source)}
    generator=Generator(analysis,original_assertions)
    for ext in tree.ext:
        if analysis.active(ext):
            output+='#line '+str(ext.coord.line)+' "'+str(filename).replace('\\','/')+'"\n'
            if isinstance(ext,C.StaticAssert):
                text=original_assertions[ext.coord.line]
                output+=text+'\n'
                continue
            text=generator.visit(ext) if lower else c_generator.CGenerator().visit(ext)
            if not isinstance(ext,(C.FuncDef,C.Pragma)):text+=';'
            output+=text+'\n'
    counts=Counter(r['status'] for r in analysis.records)
    categories=Counter(c for r in analysis.records for c in r['categories'])
    receipt={'schema':'msc16-declaration-expressions-v1','frontend':'pycparser '+pycparser.__version__+' + GCC preprocessing',
             'input_sha256':hashlib.sha256(source.encode('latin1')).hexdigest(),
             'output_sha256':hashlib.sha256(output.encode('latin1')).hexdigest(),
             'counts':dict(counts),'categories':dict(categories),'expressions':analysis.records,
             'open_domain_expressions':sum(any(c.endswith('-domain') for c in r['categories']) for r in analysis.records),
             'premises':['MinGW GCC signed char; Windows LLP64; int16 storage/casts are signed short',
                         'MSC usual arithmetic conversion and C90 literal candidate sequence',
                         'Signed overflow/invalid shifts/division trap domains are not ISO C equality claims',
                         'Header declarations are native ABI contracts, not recovered game expressions']}
    return output,receipt
