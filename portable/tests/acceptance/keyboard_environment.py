"""Admission proof for US recordings and demonstrably layout-neutral legacy tapes."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from dos.run import KEYBOARD_ENVIRONMENT, KEYBOARD_ENVIRONMENT_SHA256, keyboard_layout
from .state_schema import sha

HERE = Path(__file__).resolve().parent


def key_cases(script):
    held = set()
    cases = []
    modifiers = dict(lshift=1, rshift=1, lctrl=2, rctrl=2, lalt=4, ralt=4)
    for raw in script.read_text().splitlines():
        parts = raw.split('#', 1)[0].split()
        if len(parts) != 3 or parts[1] not in ('key', 'keydown', 'keyup'):
            continue
        _, operation, key = parts
        if key in modifiers:
            if operation == 'keydown': held.add(key)
            elif operation == 'keyup': held.discard(key)
            else: raise ValueError('Cannot prove a transient legacy modifier')
        elif operation != 'keyup':
            mask = 0
            for name in held: mask |= modifiers[name]
            cases.append(dict(key=key, modifiers=mask))
    if held: raise ValueError('Legacy recipe leaves modifiers held')
    return cases


def neutral_proof(script):
    fixtures = [HERE/('key_bios_'+layout+'.json') for layout in ('us','cz')]
    tables = [{(c['key'],c['modifiers']): c for c in json.loads(p.read_text())['cases']} for p in fixtures]
    cases = key_cases(script)
    if not cases: raise ValueError('No keyboard evidence in recipe')
    for c in cases:
        key = c['key'],c['modifiers']
        a, b = [table.get(key) for table in tables]
        if a is None or b is None or any(a[k] != b[k] for k in ('words','release_words','flags')):
            raise ValueError('Layout-sensitive or unproved transition: '+str(c))
    return dict(expected_layout='us', source_layout='cz243', script_sha256=sha(script),
                cases=cases, fixtures={p.name:sha(p) for p in fixtures},
                scope='All recipe key makes under their held modifiers have identical BIOS words, release words and flags in measured CZ243/US controls; scan positions are unchanged. No capture is relabelled US.')


def validate_keyboard(directory, manifest, recipe):
    if sha(KEYBOARD_ENVIRONMENT) != KEYBOARD_ENVIRONMENT_SHA256:
        raise ValueError('Keyboard environment pin changed')
    layout = manifest.get('keyboard_layout')
    if layout == dict(language='us',layout='us'):
        execution = json.loads((directory/'capture/execution-report.json').read_text())
        query = directory/'capture/KEYBOARD.TXT'
        host = directory/'capture/host.log'
        if (execution.get('keyboard_layout') != layout or
                sha(query) != execution.get('keyboard_layout_query',{}).get('sha256') or
                keyboard_layout(host.read_text(encoding='latin1'),query.read_text(encoding='latin1')) != layout or
                manifest.get('keyboard_environment',{}).get('sha256') != KEYBOARD_ENVIRONMENT_SHA256 or
                execution.get('keyboard_environment',{}).get('sha256') != KEYBOARD_ENVIRONMENT_SHA256):
            raise ValueError('Reference US keyboard environment is not proved')
    elif layout == dict(language='cz', layout='cz243') and manifest.get('keyboard_layout_neutral'):
        host = directory/'capture/host.log'
        if (sha(host) != manifest.get('keyboard_host_log_sha256') or
                keyboard_layout(host.read_text(encoding='latin1')) != layout or
                manifest['keyboard_layout_neutral'] != neutral_proof(ROOT/recipe['script'])):
            raise ValueError('Legacy layout-neutral proof differs')
    else:
        raise ValueError('Reference lacks pinned US layout or complete layout-neutral proof; re-record: '+str(directory))
