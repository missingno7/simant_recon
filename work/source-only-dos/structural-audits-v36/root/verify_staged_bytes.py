"""Require the index to preserve exact active proof/source file bytes."""
import hashlib
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
git=['git','-c','safe.directory=D:/Prog/simant_recon']
paths=subprocess.check_output(git+['diff','--cached','--name-only','-z'],cwd=ROOT).split(b'\0')
proofs=[p.decode('utf-8') for p in paths if p and p.startswith((b'work/source-only-dos/',b'tools/',b'tests/'))]
requests=''.join(':'+path+'\n' for path in proofs).encode('utf-8')
raw=subprocess.check_output(git+['cat-file','--batch'],input=requests,cwd=ROOT)
offset=0
for path in proofs:
    end=raw.index(b'\n',offset)
    fields=raw[offset:end].split()
    assert len(fields)==3 and fields[1]==b'blob',path
    size=int(fields[2]);start=end+1;blob=raw[start:start+size]
    live=(ROOT/path).read_bytes()
    assert blob==live,path
    assert hashlib.sha256(blob).digest()==hashlib.sha256(live).digest()
    assert raw[start+size:start+size+1]==b'\n'
    offset=start+size+1
assert offset==len(raw)
print('Staged exact proof/source bytes verified:',len(proofs),'files')
