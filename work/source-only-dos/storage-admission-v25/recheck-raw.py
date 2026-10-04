"""Root reopens complete candidate controls. No original game or build mutation."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from omf import OmfReader

CANDIDATES={
 'ant':('work/source-only-dos/storage-admission-v25/ant/worker-candidate.json','71b489a39e6dff5510b6d2d82002b541ca7f85e0702c5e30aad688af0a066697'),
 'world':('work/source-only-dos/storage-admission-v25/world/worker-candidate.json','1b4e2c7f993a0ff07705ab82fd1136084b8edbcbd5a88696a2dffea08c9cf7ed'),
 'balloon':('work/source-only-dos/storage-admission-v25/balloon/worker-candidate.json','bba037fd6ab6ff1edc52f3c4101587a18f1c10f7b1518e6862f5f659cc1bab22'),
 'experiment':('work/source-only-dos/storage-admission-v25/experiment/worker-candidate.json','6527a56cf2240d828ab866044470cd1b7e3a2bb9d5de17d6ee1d57ec6d1f3fb4'),
 'handles':('work/source-only-dos/storage-admission-v25/handles/worker-candidate.json','37837e476c4dcc9d3757542569bc156de74e237be3a7c669932e6e5d4b21665a'),
 'history':('work/source-only-dos/storage-admission-v25/history/worker-candidate.json','b2b94705d4bcb531b4792c30064c40f44e9655405a7669c7bfc0bb469286c101'),
 'mode':('work/source-only-dos/storage-admission-v25/mode/worker-candidate.json','055d1cca5f713695b69768fe60036ebbf4abea382dc84dc8c1e4e7ff1b8acd00'),
 'floor':('work/source-only-dos/storage-admission-v25/floor/worker-candidate.json','363d9d8b08e9f905543de99743ecb21a505dfe54af97e9b42355056594dba491'),
 'geometry':('work/source-only-dos/storage-admission-v25/geometry/worker-candidate.json','9e5ca84202f641c7ed16b7e3c12bf6aa1c9629d06ff0d5191da4960728e404fd'),
}
MUTABLE={'tools/source_only_dos.py','tools/dos_source_bindings.py','tools/dos_storage_contracts.py',
         'build/source-only-dos/build-report.json','work/source-only-dos/current-intake.json'}

def digest(raw):return hashlib.sha256(raw).hexdigest()
def path_for(value):
    path=Path(value.replace('\\','/'))
    path=path if path.is_absolute() else ROOT/path
    assert not path.is_relative_to(ROOT/'assets'),path
    return path
def pins(value):
    if isinstance(value,dict):
        if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):yield value
        for item in value.values():yield from pins(item)
    elif isinstance(value,list):
        for item in value:yield from pins(item)
def public_sections(raw):
    sections={'Name':{},'Value':{}};counts={'Name':0,'Value':0};section=None
    for line in raw.decode('latin1').splitlines():
        for name in sections:
            if 'Publics by '+name in line:section=name;counts[name]+=1;break
        else:
            if section:
                m=re.match(r'^\s*([0-9A-Fa-f]{4}:[0-9A-Fa-f]{4})\s+(?:(Abs|Res|Ovl)\s+)?(\S+)\s*$',line)
                if m:
                    address,kind,name=m.groups();name=name.casefold()
                    assert name not in sections[section],name
                    sections[section][name]=address.upper()
    assert counts=={'Name':1,'Value':1} and sections['Name']==sections['Value'] and sections['Name']
    return sections,counts
def shape(obj):
    return dict(module_name=obj.name,communals=obj.communals,publics=obj.publics,externals=obj.externals,
        segment_lengths=obj.segment_lengths,linker_fixups=obj.linker_fixups,
        initialized_data_hex={k:v.hex() for k,v in obj.segments.items() if k not in ('$$SYMBOLS','$$TYPES')
            and not any(s['name']==k and s['class']=='CODE' for s in obj.segment_defs)})
def review(label):
    filename,expected=CANDIDATES[label];raw=(ROOT/filename).read_bytes();assert digest(raw)==expected
    wrapper=json.loads(raw);c=wrapper.get('contract',wrapper);assert c['root_reviewed'] is False
    checked={};drift=[];objects={}
    for p in pins(wrapper):
        path=path_for(p['path']);key=(str(path),p['sha256'])
        if key in checked:continue
        data=path.read_bytes();actual=digest(data)
        relative=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        if actual!=p['sha256']:
            assert relative in MUTABLE,(p['path'],p['sha256'],actual)
            drift.append(dict(historical_pin=p,current_sha256=actual))
        else:assert 'size' not in p or len(data)==p['size'],p
        checked[key]=p
        if path.suffix.casefold()=='.obj':objects[relative]=shape(OmfReader(communals=True).read(data))
    rows=[];names={r['name'].casefold() for r in c['communals']}
    for r in c['cases']:
        rawmeta=r['raw']
        if 'full_run' in r:
            rawmeta=dict(r['full_run']);rawmeta['hex']=rawmeta.pop('raw_hex')
        rp=rawmeta['artifact_pin'];lp=r['link_pin'];mp=r['map_pin']
        run=path_for(rp['path']).read_bytes()
        assert run.hex()==rawmeta['hex'] and digest(run)==rawmeta['sha256'] and len(run)==rawmeta['size']
        marker=r.get('expected_marker',r['expected']) if 'full_run' not in r else ('PASS' if r['case']=='positive' else 'PROGRAM_NONZERO')
        assert run.endswith((marker+'\r\n').encode('ascii')),(label,r['case'],run)
        if 'actual_marker' in r:assert r['actual_marker']==marker
        assert r['actual']==r['expected'] and r['runner_exit']==0 and not r['timed_out']
        link=path_for(lp['path']).read_bytes().decode('latin1')
        assert not re.search(r'\b(?:warnings?|errors?|fatal|undefined|unresolved|aborted)\b|cannot\s+open',link,re.I),lp
        matrix,counts=public_sections(path_for(mp['path']).read_bytes())
        recorded={k:{n.casefold():a.upper() for n,a in v.items()} for k,v in r['public_address_matrix'].items()}
        # Some frozen worker schemas describe a valid owner/non-absolute
        # projection. Root keeps that fact explicit and supplies full sections
        # from the original MAP for a separate normalized admission packet.
        # This isolated contrast deliberately links one word and a separate
        # backing. The four whole-provider world cases still require all 17.
        case_names={ '_fd_50f6_0208' } if label=='world' and r['case']=='plus2_independent_saverec_backing' else names
        assert case_names<=matrix['Name'].keys()
        assert set(recorded)==set(matrix)
        assert all(matrix[k].get(n)==a for k,v in recorded.items() for n,a in v.items())
        for a in r['aliases']:
            av=matrix['Name'][a['alias'].casefold()];tv=matrix['Name'][a['target'].casefold()]
            aseg,aoff=[int(x,16) for x in av.split(':')];tseg,toff=[int(x,16) for x in tv.split(':')]
            assert aseg==tseg and aoff-toff==a['delta']
        rows.append(dict(linker=r['linker'],case=r['case'],raw=rawmeta,marker=marker,link_pin=lp,map_pin=mp,
            public_count={k:len(v) for k,v in matrix.items()},map_headings=counts,aliases=r['aliases'],
            public_address_matrix=matrix,worker_matrix_was_complete=(matrix==recorded)))
    assert {(r['linker'],r['case']) for r in rows}=={(p,cname) for p in ('rtlink400','rtlink610') for cname in c['required_cases']}
    out=dict(candidate=filename,candidate_sha256=expected,module=c['module'],immutable_pin_count=len(checked)-len(drift),
             historical_observation_drift=drift,cases=rows,actual_objects=objects,root_admitted=False)
    (output/(label+'-raw-review.json')).write_bytes((json.dumps(out,indent=2)+'\n').encode())
    print(label,'PASS',len(checked)-len(drift),'immutable pins,',len(rows),'complete raw cases,',len(objects),'actual OMFs;',len(drift),'historical observations')

if __name__=='__main__':
    output=ROOT/'build/workers/dos_v25_preserved_raw_recheck'
    output.mkdir(parents=True,exist_ok=True)
    for label in CANDIDATES:review(label)
