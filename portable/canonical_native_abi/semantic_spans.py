"""Realize reviewed DOS cross-owner spans as native storage, never game rewrites.

Member extents are canonical declarations/COMDEFs, positions are canonical MAP
facts. A gap is an error. Initializers come only from the converted canonical TU.
GNU assembler aliases preserve every TU's original consumer declaration and all
address/index/block-I/O expressions. The packed object exposes typed DWARF fields.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, json, re
from . import tokenizer
from .lexical import mask_literals
from .source_views import top_level_statements, TRIVIA


def source_consumers(texts, names):
    """All executable/initializer references, excluding declarator identifiers."""
    rows=[]
    for path,text in sorted(texts.items()):
        declarations=[]
        for lo,hi in top_level_statements(text):
            part=text[lo:hi]
            tokens=[t for t in tokenizer.tokenize(part) if t.kind not in TRIVIA]
            end=next((t.s for t in tokens if t.text=='='),len(part))
            declarations.append((lo,lo+end))
        for token in tokenizer.tokenize(text):
            if token.kind!='id' or token.text not in names:continue
            if any(lo<=token.s<hi for lo,hi in declarations):continue
            rows.append(dict(file=path,line=text.count('\n',0,token.s)+1,
                             owner=token.text))
    return rows


def save_records(text):
    start=re.search(r'struct SaveRec far fd_4E4B_0000\[\d+\] = \{',text)
    if not start:raise ValueError('canonical SaveRec table missing')
    body=text[start.start():text.index('};',start.start())]
    rows=[]
    for index,(size,count,data) in enumerate(re.findall(r'\{\s*([^,{}]+),\s*([^,{}]+),\s*([^{}]+?)\s*\}',body)):
        size,count=int(size,0),int(count,0)
        if not count:break
        expression=re.sub(r'\(void far \*\)\s*&?','',data).strip()
        match=re.fullmatch(r'\((\w+) \+ (\d+)\)',expression)
        owner,extra=(match[1],int(match[2])) if match else (expression,0)
        rows.append(dict(record=index,owner=owner,extra=extra,bytes=size*count))
    return rows


def cover(layout,start,length):
    """Tile the actual requested bytes with explicit complete canonical owners."""
    members=[];cursor=start;end=start+length
    while cursor<end:
        hits=[(name,f) for name,f in layout.items() if f['address']<=cursor<f['address']+f['bytes']]
        if len(hits)!=1:raise ValueError(f'unproved span byte {cursor:#x}: {hits}')
        name,f=hits[0];members.append(name);cursor=min(end,f['address']+f['bytes'])
    return members


class Contracts:
    def __init__(self,root,texts,document=None):
        self.root=Path(root)
        self.document=document or json.loads((self.root/'portable/semantic-spans.json').read_text())
        self.spans=self.document['spans'];self.layout=self.document['owner_layout']
        self.names={m['owner'] for s in self.spans for m in s['members']}
        self.definitions={};self.sources={};self.initializers={}
        if self.document['schema']!='simant-semantic-spans-v1':raise ValueError('unsupported semantic span schema')
        for name,fact in self.layout.items():
            path=fact['source']
            if hashlib.sha256(texts[path].encode('latin1')).hexdigest()!=fact['source_sha256']:
                raise ValueError('span layout source changed: '+path)
        seen=set()
        for span in self.spans:
            cursor=0
            for member in span['members']:
                name=member['owner'];fact=self.layout.get(name)
                if not fact:raise ValueError('span member missing layout evidence: '+name)
                if name in seen:raise ValueError('span member duplicated: '+name)
                seen.add(name)
                if member['offset']!=cursor or member['bytes']!=fact['bytes'] or fact['address']-span['dos_address']!=cursor:
                    raise ValueError('span offset/size contradicts canonical layout: '+name)
                cursor+=member['bytes']
            if cursor!=span['bytes']:raise ValueError('span extent does not tile its owners: '+span['id'])
            actual=source_consumers(texts,{m['owner'] for m in span['members']})
            if actual!=span['consumers']:raise ValueError('consumer appears outside declared span or stale census: '+span['id'])
        # Independently enumerate ALL SaveRec blocks. Deleting a contract does
        # not delete its requirement, and a new block cannot silently escape it.
        aliases=self.document['aliases']
        self.cross_records=[]
        for row in save_records(texts['src/S09/m35F5.c']):
            name=row['owner'];extra=row['extra']
            if name in aliases:
                extra+=aliases[name]['offset'];name=aliases[name]['owner']
            if name not in self.layout:raise ValueError('SaveRec owner lacks extent evidence: '+name)
            start=self.layout[name]['address']+extra
            owners=cover(self.layout,start,row['bytes'])
            if len(owners)>1:
                matches=[s for s in self.spans if set(owners)<={m['owner'] for m in s['members']}]
                if len(matches)!=1:raise ValueError('SaveRec cross-owner span undeclared: '+str(row['record']))
                self.cross_records.append(dict(row,span=matches[0]['id'],owners=owners))
        # Whole-canonical literal index census. Width is the consumer's DOS
        # declaration, not the defining byte owner's element type.
        self.cross_accesses=[]
        for path,text in sorted(texts.items()):
            clean=mask_literals(text)
            declaration_ranges=[]
            for lo,hi in top_level_statements(text):
                eq=text.find('=',lo,hi)
                declaration_ranges.append((lo,eq if eq>=0 else hi))
            for match in re.finditer(r'\bextern\s+((?:unsigned\s+|signed\s+)?(?:int|short|long|char)\s+(?:far\s+)?)(\w+)\s*\[',clean):
                name=match[2]
                if name not in self.layout:continue
                width=1 if 'char' in match[1] else 4 if 'long' in match[1] else 2
                for use in re.finditer(r'\b'+re.escape(name)+r'\s*\[\s*(-?(?:0x[\da-fA-F]+|\d+))\s*\]',clean):
                    if any(lo<=use.start()<hi for lo,hi in declaration_ranges):continue
                    index=int(use[1],0)
                    if 0<=index and (index+1)*width<=self.layout[name]['bytes']:continue
                    # Negative indexes in supported-domain exclusions remain
                    # explicit debt; this contract realizes proven positive
                    # cross-owner literal accesses, not arbitrary DOS memory.
                    if index<0:continue
                    start=self.layout[name]['address']+index*width
                    owners=cover(self.layout,start,width)
                    matches=[s for s in self.spans if name in {m['owner'] for m in s['members']} and set(owners)<={m['owner'] for m in s['members']}]
                    if len(matches)!=1:raise ValueError(f'canonical indexed consumer outside declared spans: {path}:{text.count(chr(10),0,use.start())+1} {use[0]}')
                    self.cross_accesses.append(dict(file=path,line=text.count('\n',0,use.start())+1,owner=name,index=index,span=matches[0]['id']))

    def extract(self,path,text):
        """Replace storage declarations only; keep uses/consumer types intact."""
        edits=[]
        for lo,hi in top_level_statements(text):
            part=text[lo:hi];tokens=[t for t in tokenizer.tokenize(part) if t.kind not in TRIVIA]
            if not tokens:continue
            eq=next((t.s for t in tokens if t.text=='='),len(part))
            ids={t.text for t in tokens if t.kind=='id' and t.s<eq}
            hit=ids&self.names
            if not hit or 'extern' in ids or 'typedef' in ids:continue
            if len(hit)!=1:raise ValueError('span storage declaration shape ambiguous: '+path)
            name=hit.pop()
            if name in self.definitions:raise ValueError('multiple native span owners: '+name)
            first=tokens[0].s
            declaration=part[first:eq].strip().rstrip(';').strip()
            self.definitions[name]=declaration+';';self.sources[name]=path
            self.initializers[name]=part[eq+1:].strip().rstrip(';').strip() if eq<len(part) else '{0}'
            edits.append((lo,hi,part[:first]+'extern '+declaration+';'))
        for lo,hi,replacement in reversed(edits):text=text[:lo]+replacement+text[hi:]
        return text

    def emit(self,out):
        missing=self.names-self.definitions.keys()
        if missing:raise ValueError('canonical span member storage missing: '+str(sorted(missing)))
        lines=['#include <stdint.h>','#include <stddef.h>',
               '/* Canonical owner initializers; no copied executable bytes. */']
        bindings={}
        for span in self.spans:
            group='semantic_span_'+re.sub(r'\W','_',span['id'])
            tag=group+'_storage'
            lines+=['struct __attribute__((packed,aligned(2))) '+tag+' {']
            lines += ['    '+self.definitions[m['owner']] for m in span['members']]
            lines+=['};','struct '+tag+' '+group+' = {']
            lines+=['    .'+m['owner']+' = '+self.initializers[m['owner']]+',' for m in span['members']]
            lines+=['};',f'_Static_assert(sizeof(struct {tag}) == {span["bytes"]}, "span extent: {span["id"]}");']
            for member in span['members']:
                name=member['owner'];offset=member['offset'];size=member['bytes']
                lines += [f'_Static_assert(offsetof(struct {tag}, {name}) == {offset}, "span offset: {name}");',
                          f'_Static_assert(sizeof((({tag_placeholder(tag)})0)->{name}) == {size}, "span size: {name}");',
                          f'__asm__(".globl {name}\\n.set {name}, {group}+{offset}\\n");']
                bindings[name]=dict(expression=group+'.'+name,offset=offset,bytes=size,group=group)
        path=Path(out)/'canonical_semantic_spans.c';path.write_text('\n'.join(lines)+'\n')
        receipt=dict(schema='simant-native-span-realization-v1',spans=[s['id'] for s in self.spans],
                     bindings=bindings,cross_owner_save_records=self.cross_records,
                     cross_owner_literal_accesses=self.cross_accesses,mechanism='packed canonical owner group + exported offset aliases; no access-site rewrites')
        (Path(out)/'semantic-spans.json').write_text(json.dumps(receipt,indent=2)+'\n')
        return path,receipt


def tag_placeholder(tag):
    return 'struct '+tag+' *'
