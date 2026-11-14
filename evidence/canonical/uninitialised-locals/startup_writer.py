from pathlib import Path
import json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
root=Path(__file__).resolve().parents[3];receipt=json.loads((root/'evidence/canonical/uninitialised-locals/stamp-origin.json').read_text());rows=[]
for obs in receipt['observations']:
 if obs['variant'] not in ('original-reference','canonical-reference'):continue
 frame=root/obs['frames']['before']['path'];m=frame.read_bytes();reg=obs['frames']['before']['registers'];cs=int(reg['cs'],16);pc=16*cs+int(reg['eip'],16)
 # This entire CRT scan/descriptor-loop span has no intervening C calls.
 start=16*cs+(0x169 if obs['target']=='original' else 0x15f)
 decoded=[dict(pc=hex(x.address),instruction=x.mnemonic+' '+x.op_str) for x in Cs(CS_ARCH_X86,CS_MODE_16).disasm(m[start:pc+2],start)]
 rows.append(dict(target=obs['target'],frame_sha256=obs['frames']['before']['sha256'],instructions=decoded))
source=Path('C:/tools/dosbox-x-2026.08.31-simant-acceptance-observation-src/src/dos/dos.cpp');lines=source.read_text(encoding='utf8').splitlines()
manifest=json.loads((root/'layout/manifest.json').read_text());unit=manifest['modules']['root:15F8']
result=dict(schema='startup-register-save-writer-v1',crt_scans=rows,canonical_object=dict(module='root:15F8',source=unit['source'],profile=unit['profile'],flags=unit['flags'],object_sha256=unit['object_sha256']),dos_handler=dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),excerpt_first_line=1053,excerpt=lines[1052:1065]),reason='Before INT SP=A4CEh. Hardware INT pushes 6 bytes. DOS writes BX at callback SP-16=A4B8h and CX at callback SP-14=A4BAh. After five main argument words, far call and saved BP, main BP=A4C2h, so these are BP-0Ah and BP-8. Canonical has the same relative arithmetic with its independent frame offsets.')
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.parent.mkdir(parents=True,exist_ok=True)
args.out.write_text(json.dumps(result,indent=2)+'\n')
