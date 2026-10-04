"""Root reopens complete candidate controls. No original game or build mutation."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from omf import OmfReader
from dos_storage_policies_v27 import policy, POLICY_PINS

CANDIDATES={
 'delay':('build/workers/dos_delay_word_independent_v33/contract-v33.json','9fb00bc18f60cb379e05359eb829e2938ebc16dcfe5a1b0a8c38015df2a53b24'),
 'sound':('build/workers/dos_sound_storage_independent_v31/generic-storage-contract-candidate-v31.json','e1d8a2998b8b8f23a47338e8c78c96fac765f76748415ae9f61e88345c6fb652'),
 'handles':('build/workers/dos_window_handle_independent_v31/contract-v31.json','b94e49c67aadac10c4f23b41fb0c3ebf37f38168bd7b4b86a51c74e58fb92567'),
 'misc':('build/workers/dos_misc_storage_independent_v31/generic-contract-v31.json','e0db323b417e1b91fe8042b1426155fd9b14cb79ea31b2448b283833045bfa70'),
}

SUPPORT_PINS={'misc': [{'path': 'build/workers/dos_misc_storage_independent_v31/compile-evidence-v31.json', 'sha256': '02f8a513b830ab2073de24e125e1aef427e6e14298e33426cec81497b89bd3ef', 'size': 38608}], 'delay': [{'path': 'build/workers/dos_delay_word_owner_v32/runtime/probe-v32.json', 'sha256': 'd758b75e10b3577e0c4dee901010a62e80a33cc051ff9e903bd9b97a51111021', 'size': 123979}, {'path': 'build/workers/dos_delay_word_owner_v33/source-addendum-v33.json', 'sha256': 'a6fad53037d90f7dca76828a1c45a73569eb8e8877736dbf0be90b303dde990a', 'size': 16858}]}
MUTABLE={'tools/source_only_dos.py','tools/dos_source_bindings.py','tools/dos_storage_contracts.py',
         'build/source-only-dos/build-report.json','work/source-only-dos/current-intake.json','docs/source-only-dos.md'}

def digest(raw):return hashlib.sha256(raw).hexdigest()
def path_for(value):
    path=Path(value.replace('\\','/'))
    path=path if path.is_absolute() else ROOT/path
    # Resource identity checks are research metadata, never provider initializers.
    assert not (path.is_relative_to(ROOT/'assets') and path.suffix.casefold()=='.exe'),path
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
def shape(obj, include_debug=False):
    return dict(module_name=obj.name,communals=obj.communals,publics=obj.publics,externals=obj.externals,
        segment_lengths=obj.segment_lengths,linker_fixups=obj.linker_fixups,
        initialized_data_hex={k:(v.hex().upper() if include_debug else v.hex()) for k,v in obj.segments.items() if (include_debug or k not in ('$$SYMBOLS','$$TYPES'))
            and not any(s['name']==k and s['class']=='CODE' for s in obj.segment_defs)})
def review(label):
    filename,expected=CANDIDATES[label];raw=(ROOT/filename).read_bytes();assert digest(raw)==expected
    wrapper=json.loads(raw);c=wrapper.get('contract',wrapper);assert c['root_reviewed'] is False
    checked={};drift=[];objects={}
    supplementary=[]
    for metadata in SUPPORT_PINS.get(label,[]):
        raw_support=path_for(metadata['path']).read_bytes()
        assert digest(raw_support)==metadata['sha256'] and len(raw_support)==metadata['size']
        supplementary.extend([metadata,json.loads(raw_support)])
    for p in pins([wrapper,supplementary]):
        path=path_for(p['path']);key=(str(path),p['sha256'])
        if key in checked:continue
        data=path.read_bytes();actual=digest(data)
        relative=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        if actual!=p['sha256']:
            assert relative in MUTABLE,(p['path'],p['sha256'],actual)
            drift.append(dict(historical_pin=p,current_sha256=actual))
        else:assert 'size' not in p or len(data)==p['size'],p
        checked[key]=p
        if path.suffix.casefold()=='.obj':objects[relative]=shape(OmfReader(communals=True).read(data),include_debug=(label=='delay'))
    rows=[];names={r['name'].casefold() for r in c['communals']}
    for r in c['cases']:
        rawmeta=r['raw']
        if 'full_run' in r:
            rawmeta=dict(r['full_run']);rawmeta['hex']=rawmeta.pop('raw_hex')
        rp=rawmeta['artifact_pin'];lp=r['link_pin'];mp=r['map_pin']
        run=path_for(rp['path']).read_bytes()
        assert run.hex()==rawmeta['hex'] and digest(run)==rawmeta['sha256'] and len(run)==rawmeta['size']
        module={'handles':'source-owned:window-ralloc-handles','misc':'source-owned:remaining-misc-storage','sound':'source-owned:remaining-sound-storage','delay':'source-owned:render-delay-word'}[label]
        literal_path=ROOT/POLICY_PINS[label]['path']
        assert digest(literal_path.read_bytes())==POLICY_PINS[label]['sha256']
        literal=policy(module,c['communals'])
        marker=literal['required_cases'][r['case']]
        pattern=literal.get('raw_patterns',{}).get(r['case'])
        if pattern is not None:
            assert re.fullmatch(pattern,run.decode('ascii')) is not None,(label,r['case'])
        else:
            expected_raw=literal.get('raw_text',{}).get(r['case'],marker+'\r\n').encode('ascii')
            assert run==expected_raw,(label,r['case'],run,expected_raw)
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
             historical_observation_drift=drift,cases=rows,actual_objects=objects,supplementary_pins=SUPPORT_PINS.get(label,[]),root_admitted=False)
    output=ROOT/'build/workers/dos_root_recheck_v27'
    output.mkdir(parents=True,exist_ok=True)
    (output/(label+'-raw-review.json')).write_bytes((json.dumps(out,indent=2)+'\n').encode())
    print(label,'PASS',len(checked)-len(drift),'immutable pins,',len(rows),'complete raw cases,',len(objects),'actual OMFs;',len(drift),'historical observations')

if __name__=='__main__':
    for label in CANDIDATES:review(label)
