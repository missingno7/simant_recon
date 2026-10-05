"""Bounded object frame classification, not byte matching or domain closure."""
from pathlib import Path
import hashlib
import json
import sys
import argparse

ROOT=Path(__file__).resolve().parents[3]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',type=Path,required=True)
OUT=parser.parse_args().out.resolve()
build=(ROOT/'build').resolve()
OUT.relative_to(build)
if OUT==build or (OUT.exists() and any(OUT.iterdir())):
    raise ValueError('--out must be a fresh subdirectory under build/')
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools'))
import compiler
from omf import OmfReader
compiler.WORK=OUT/'frame_compile'
program=json.loads((ROOT/'src/program.json').read_text())
report={'schema':'current29-asm-omf-frame-review-v1','scope':'Parse complete current ASM objects for source-placement offset frame inconsistencies. No original input or byte comparison, no execution/domain completeness claim.','modules':[]}
for item in program['modules']:
    if item['lang']!='asm':
        continue
    path=ROOT/item['source']
    body=path.read_bytes()
    source=body.decode('ascii')
    result=compiler.assemble(source,item['profile'],item['flags'],basename='FRAME',keep=True)
    assert result.ok,(item['key'],result.log)
    obj=OmfReader(communals=True).read(result.obj)
    classes={definition['name']:definition.get('class') for definition in obj.segment_defs}
    # A _DATA segment-frame or group-framed own CODE offset deserves source review.
    suspect=[f for f in obj.linker_fixups if f['loc']=='offset16' and not f['self_relative'] and
      ((f['target']=='_DATA' and f['frame_kind']=='segment') or
       (classes.get(f['target'])=='CODE' and f['frame_kind']=='group'))]
    row={'key':item['key'],'source':item['source'],'sha256':hashlib.sha256(body).hexdigest(),
      'inventory_hash_matches':hashlib.sha256(body).hexdigest()==item['source_sha256'],
      'segment_lengths':obj.segment_lengths,'fixup_count':len(obj.linker_fixups),
      'suspect_data_segment_or_code_group_offset_frames':suspect}
    report['modules'].append(row)
    print(item['key'],'fixups',len(obj.linker_fixups),'review candidates',len(suspect),flush=True)
    for fx in suspect:
        print(' ',fx['segment'],hex(fx['offset']),fx['target'],fx['displacement'],fx['frame_kind'],fx['frame'],flush=True)
(OUT/'current29_omf_frame_receipt.json').write_text(json.dumps(report,indent=2)+'\n')
