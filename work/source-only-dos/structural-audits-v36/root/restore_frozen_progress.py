"""Restore only verified generated-date drift; never refresh frozen pins."""
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
git=['git','-c','safe.directory=D:/Prog/simant_recon','show']
old=subprocess.check_output(git+['HEAD:docs/progress.json'],cwd=ROOT)
before=json.loads(old); current=json.loads((ROOT/'docs/progress.json').read_bytes())
assert current['validation']=='PASS' and current['failures']==[]
assert {k:v for k,v in current.items() if k!='generated'}=={k:v for k,v in before.items() if k!='generated'}
(ROOT/'docs/progress.json').write_bytes(old)
old_md=subprocess.check_output(git+['HEAD:docs/progress.md'],cwd=ROOT)
new_md=(ROOT/'docs/progress.md').read_bytes().replace(b'\r\n',b'\n')
assert new_md.replace(current['generated'].encode(),before['generated'].encode())==old_md.replace(b'\r\n',b'\n')
(ROOT/'docs/progress.md').write_bytes(old_md)
print('Frozen progress restored after verified date-only drift.')
