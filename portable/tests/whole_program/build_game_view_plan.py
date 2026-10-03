"""Create the bounded proposal once from exact original declaration views."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
names = ['fd_50F6_' + n for n in
    ('10CC', '10DA', '10E2', '10E6', '10EA', '10EE', '10D2', '1104', '110C')]
plan = {'schema': 'simant-native-game-view-state-v1',
    'claim': 'Native source-bounded storage only; no historical ownership claim',
    'sources': {}, 'owners': []}
for name in names:
    rect = name[-4:] in ('10D2', '1104', '110C')
    owner = {'name': name, 'kind': 'rectangle' if rect else 'handle-cell',
        'source_extent': 8 if rect else 4,
        'extent_basis': 'complete struct Rect declaration' if rect else
                        'one source Handle (two DOS pointer words)',
        'declarations': []}
    for path in sorted((ROOT / 'src').rglob('*.c')):
        rel = path.relative_to(ROOT).as_posix()
        for line, text in enumerate(path.read_text().splitlines(), 1):
            if not re.fullmatch(r'extern\s+[^;]*\b' + name + r'\b[^;]*;', text.strip()):
                continue
            decl = text.strip()
            storage = 'native_game_' + name
            if rect:
                if 'struct Rect' in decl:
                    view = f'(*((struct Rect *){storage}.raw))'
                elif 'Point' in decl:
                    view = f'(*((Point *){storage}.raw))'
                elif re.search(r'\bint\s+far\s+' + name + r'\[2\]', decl):
                    view = storage + '.words'
                else:
                    raise ValueError(decl)
            elif name.endswith('10CC'):
                view = storage if '[]' in decl else storage + '[0]'
            else:
                view = storage
            owner['declarations'].append({'source': rel, 'line': line,
                'text': decl, 'native_view': view})
            plan['sources'][rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not owner['declarations']:
        raise ValueError(name)
    plan['owners'].append(owner)
target = ROOT / 'portable/research/game_view_state_v1.json'
if target.exists():
    raise ValueError('proposal is immutable; use a new version')
target.write_text(json.dumps(plan, indent=2) + '\n')
print(target)
