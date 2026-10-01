from pathlib import Path
import re
base=Path(__file__).with_name('base.c').read_text(encoding='latin1')
outdir=Path(__file__).with_name('round2-sources');outdir.mkdir(exist_ok=True)
func='int far LessonDone(int lesson)\n{'
pos=base.index(func)
pre, tail=base[:pos],base[pos:]
old='''    case 54:
        if (MePlane == 3) {
            fd_50F6_1074 = 0;
            return 1;
        }
        if (MePlane == 2) {
            fd_50F6_1074 = 1;
            return 1;
        }
        return 0;
    case 55:
'''
assert tail.count(old)==1
repls={
'case54_shared_return': '''    case 54:
        if (MePlane == 3)
            fd_50F6_1074 = 0;
        else if (MePlane == 2)
            fd_50F6_1074 = 1;
        else
            return 0;
        return 1;
    case 55:
''',
'case54_nested_switch_returns': '''    case 54:
        switch (MePlane) {
        case 3:
            fd_50F6_1074 = 0;
            return 1;
        case 2:
            fd_50F6_1074 = 1;
            return 1;
        }
        return 0;
    case 55:
''',
'case54_nested_switch_shared_return': '''    case 54:
        switch (MePlane) {
        case 3:
            fd_50F6_1074 = 0;
            break;
        case 2:
            fd_50F6_1074 = 1;
            break;
        default:
            return 0;
        }
        return 1;
    case 55:
''',
'case54_result_local_lifetime': '''    case 54: {
        int done;
        if (MePlane == 3) {
            fd_50F6_1074 = 0;
            done = 1;
        } else if (MePlane == 2) {
            fd_50F6_1074 = 1;
            done = 1;
        } else {
            done = 0;
        }
        return done;
    }
    case 55:
''',
}
for name,repl in repls.items():
 (outdir/(name+'.c')).write_text(pre+tail.replace(old,repl),encoding='latin1',newline='')
(outdir/'base.c').write_text(base,encoding='latin1',newline='')
for name,marker,prefix in [
 ('outer_default_first','    case 1:\n','    default:\n        return 0;\n'),
 ('outer_default_last','    case 56:\n','')]:
 if name=='outer_default_first':
  src=base
  p=src.index(func); head,rest=src[:p],src[p:]
  assert marker in rest
  src=head+rest.replace(marker,prefix+marker,1)
 else:
  src=base
  p=src.index(func); head,rest=src[:p],src[p:]
  # Place a default return directly after case 56's return, just before the switch closes.
  m='''    case 56:
        return 1;
    }
'''
  assert rest.count(m)==1
  src=head+rest.replace(m,'''    case 56:
        return 1;
    default:
        return 0;
    }
''',1)
 (outdir/(name+'.c')).write_text(src,encoding='latin1',newline='')
# Contrast: explicit default break immediately before case 56; same behavior as dispatching to shared false return.
marker='    case 56:\n'
p=base.index(func);head,rest=base[:p],base[p:]
assert rest.count(marker)==1
(outdir/'outer_default_break.c').write_text(head+rest.replace(marker,'    default:\n        break;\n'+marker,1),encoding='latin1',newline='')
