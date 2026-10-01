from pathlib import Path
base_path=Path(__file__).with_name('base.c')
base=base_path.read_text(encoding='latin1')
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
assert base.count(old)==1
variants={
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
}
for name,repl in variants.items():
 out=Path(__file__).with_name(name+'.c')
 out.write_text(base.replace(old,repl),encoding='latin1',newline='')
for name, marker in [('outer_default_first','    case 1:\n'),('outer_default_last','    case 56:\n')]:
 repl='    default:\n        return 0;\n'+marker
 out=Path(__file__).with_name(name+'.c')
 out.write_text(base.replace(marker,repl,1),encoding='latin1',newline='')
# A semantically redundant explicit default-break is the negative contrast to return0.
marker='    case 56:\n'
out=Path(__file__).with_name('outer_default_break.c')
out.write_text(base.replace(marker,'    default:\n        break;\n'+marker,1),encoding='latin1',newline='')
