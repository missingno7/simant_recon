"""Install only root-written literal policies, never candidate-derived shapes."""
from pathlib import Path
from pprint import pformat
import json
from screen_policy import policy as screen_policy
from word_policy import policy as word_policy
ROOT = Path(__file__).resolve().parents[3]

def main():
    policies = {row['module']: row for row in (screen_policy(), word_policy())}
    text = '''"""Independent root policies for typed screen and FAR state owners.

Literal controls encode fresh test-owned integer fields and fixups. They never
read candidates, original images, historical debt bytes or object capsules.
"""
from copy import deepcopy

POLICIES = ''' + pformat(policies, width=100, sort_dicts=False) + '''

CONTRACTS = {module: (
    'screen_clip_list_contract' if module == 'source-owned:screen-clip-list'
    else 'remaining_far_state_words_contract', row['required_cases'])
    for module, row in POLICIES.items()}

def policy(module):
    return deepcopy(POLICIES[module])
'''
    (ROOT / 'tools/dos_storage_policies_v29.py').write_bytes(text.encode('ascii'))
    for label, module in [('screen', 'source-owned:screen-clip-list'), ('words', 'source-owned:remaining-far-state-words')]:
        (Path(__file__).parent / (label + '-literal-policy.json')).write_bytes(
            (json.dumps(policies[module], indent=2) + '\n').encode())

if __name__ == '__main__':
    main()
