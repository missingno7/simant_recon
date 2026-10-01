from pathlib import Path
import re
base=Path(__file__).with_name('base.c').read_text(encoding='latin1')
name='int far LessonDone(int lesson)\n{'; pos=base.index(name); pre,fn=base[:pos],base[pos:]
markers=list(re.finditer(r'    case (\d+):\n',fn))
tailmark='    }\n    return 0;\n}'
assert len(markers)==56 and fn.count(tailmark)==1
head=fn[:markers[0].start()]
body_end=fn.index(tailmark,markers[-1].end())
tail=fn[body_end:]
cases={}
for i,m in enumerate(markers):
 end=markers[i+1].start() if i+1<len(markers) else body_end
 cases[int(m.group(1))]=fn[m.start():end]
assert set(cases)==set(range(1,57))
groups=[
 [1,2,6,11,15,17,23,25,28,29,31,34,35,37,40,44,45,48,51,53,55,56],
 [3,4],[9],[10,32,42],[13],[14],[16],[18],[5,20],[21],[19,22],[24],
 [7,26],[27],[30],[8,43,46,50],[33],[36],[38],[39],[41],[47],[12,49],[52],[54]
]
order=[n for g in groups for n in g]
assert sorted(order)==list(range(1,57))
# Order all source blocks by their destination in the embedded switch table.
reordered=''.join(cases[n] for n in order)
Path(__file__).with_name('reordered_target_block_order.c').write_text(pre+head+reordered+tail,encoding='latin1',newline='')
# Also place exact repeated-body groups together in that target-address order.
shared=[]
for g in groups:
 if len(g)>1:
  # The original groups in this listing share one destination and are semantically identical.
  first=cases[g[0]]
  # Preserve the body once, with all case labels as a C fall-through group.
  for n in g:
   m=re.match(r'    case \d+:\n',cases[n]); assert m
  shared.extend('    case '+str(n)+':\n' for n in g)
  shared.append(first[first.index('\n')+1:])
 else: shared.append(cases[g[0]])
Path(__file__).with_name('reordered_target_groups.c').write_text(pre+head+''.join(shared)+tail,encoding='latin1',newline='')
Path(__file__).with_name('base.c').write_text(base,encoding='latin1',newline='')
from shutil import copyfile
outdir=Path(__file__).with_name('round3-sources');outdir.mkdir(exist_ok=True)
for nm in ['base.c','reordered_target_block_order.c','reordered_target_groups.c']:
 copyfile(Path(__file__).with_name(nm),outdir/nm)
