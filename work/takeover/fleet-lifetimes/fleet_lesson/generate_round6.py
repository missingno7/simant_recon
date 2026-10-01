from pathlib import Path
import re
base=Path(__file__).with_name('base.c').read_text(encoding='latin1')
start=base.index('int far LessonDone(int lesson)\n{');head,fn=base[:start],base[start:]
assert fn.count('switch (lesson)')==1
fn=fn.replace('switch (lesson)','switch (lesson - 1)',1)
fn,n=re.subn(r'    case (\d+):',lambda m:'    case '+str(int(m.group(1))-1)+':',fn)
assert n==56
Path(__file__).with_name('case0_based_expression.c').write_text(head+fn,encoding='latin1',newline='')
from shutil import copyfile
outdir=Path(__file__).with_name('round6-sources');outdir.mkdir(exist_ok=True)
for nm in ['base.c','case0_based_expression.c']:
 copyfile(Path(__file__).with_name(nm),outdir/nm)
