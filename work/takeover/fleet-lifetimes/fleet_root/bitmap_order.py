from pathlib import Path
import sys
sys.path.insert(0,'tools')
import csrc

root=Path('build/workers/fleet_root')
base=Path('work/takeover/residue-controls/bitmap-original-order.c').read_text(encoding='utf-8')
f=csrc.Source(base).function('win_DrawBitMap')
text=(base[:f.head_s] +
      '/* SCAFFOLD BEGIN: win_DrawBitMap remains inexact (675 vs 663 bytes).\n'
      ' * Register and stack-home allocation remain unresolved.\n'
      ' * This module follows original function order; no new code is claimed. */\n' +
      base[f.head_s:f.body.e] + '\n/* SCAFFOLD END */\n' + base[f.body.e:])
text=text.replace('\n\n\n\n/* `start`','\n\n/* `start`')
(root/'bitmap-order.c').write_text(text,encoding='utf-8',newline='\n')
print(root/'bitmap-order.c')
