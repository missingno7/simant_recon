"""Project reviewed DOS AX return contracts into native C definitions.

The canonical source deliberately contains void/implicit register returns.
Only instruction-proven contracts in the evidence inventory are projected;
unknown residue is never assigned a convenient native constant.
"""
import json
from pathlib import Path
from .lexical import function_heads
from .tokenizer import tokenize

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / 'evidence/canonical/native-register-returns/contracts.json'

def tokens(text):
    return [t.text for t in tokenize(text) if t.kind not in {'ws','nl','cmt'}]

def adapt(source, path, contracts=None):
    contracts = json.loads(CONTRACT_PATH.read_text())['repairs'] if contracts is None else contracts
    selected = [r for r in contracts if r['source'] == path]
    heads = {h['name']:h for h in function_heads(source)}
    edits = []; receipt = []
    for row in selected:
        head = heads.get(row['function'])
        if head is None: raise ValueError('missing register-return definition: '+row['function'])
        start,end = head['start'],head['end']
        before = source[start:end]
        if tokens(before) != tokens(row['native_before']):
            raise ValueError('register-return definition drift: '+row['function'])
        edits.append((start,end,row['native_after']))
        receipt.append(dict(function=row['function'],contract=row['contract'],
                            instruction_evidence=row['instruction_evidence']))
    for start,end,value in reversed(sorted(edits)):
        source = source[:start]+value+source[end:]
    return source,receipt
