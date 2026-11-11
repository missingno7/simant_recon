"""Refresh the port's pins on canonical sources after a reconstruction change.

    python portable/refresh_pins.py            # check and rewrite
    python portable/refresh_pins.py --check    # report only, exit 1 if stale

The port adapts to the reconstruction, never the reverse.  Two port contracts pin
canonical source text so that a change under them is noticed:

* ``portable/semantic-spans.json``: the source hash of every file that owns a
  cross-object data span, and the file/line census of the span's consumers;
* ``evidence/canonical/native-word-intermediates/contracts.json``: the source hash
  of each routine with an instruction-backed 16-bit intermediate.

A refresh is accepted only when the pinned facts themselves are unchanged: every
span keeps the same consumer occurrences per file and owner (only line numbers
may move), and every pinned routine is token-identical to the committed one.
Anything else is a real change to a port contract and is reported, not rewritten.
"""
import collections
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'portable'))
sys.path.insert(0, str(ROOT / 'tools'))
from canonical_native_abi import semantic_spans  # noqa: E402
import canonical  # noqa: E402

SPANS = ROOT / 'portable/semantic-spans.json'
WORDS = ROOT / 'evidence/canonical/native-word-intermediates/contracts.json'


def sha_file(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def sha_text(rel):
    return hashlib.sha256((ROOT / rel).read_text(encoding='latin1').encode('latin1')).hexdigest()


def write_like(path, document, raw):
    newline = '\r\n' if '\r\n' in raw else '\n'
    first = raw.split('\n')[1]
    indent = len(first) - len(first.lstrip())
    path.write_text(json.dumps(document, indent=indent) + '\n', encoding='utf-8', newline=newline)


def refresh_spans(check):
    raw = SPANS.read_text(encoding='utf-8')
    document = json.loads(raw)
    program = json.loads((ROOT / 'src/program.json').read_text())
    texts = {m['source']: (ROOT / m['source']).read_text(encoding='latin1')
             for m in program['modules'] if m['lang'] == 'c'}
    changed, problems = [], []
    for name, fact in document['owner_layout'].items():
        current = sha_text(fact['source'])
        if current != fact['source_sha256']:
            fact['source_sha256'] = current
            changed.append('owner source ' + fact['source'])
    for span in document['spans']:
        actual = semantic_spans.source_consumers(texts, {m['owner'] for m in span['members']})
        if actual == span['consumers']:
            continue
        key = lambda rows: collections.Counter((c['file'], c['owner']) for c in rows)
        if key(actual) != key(span['consumers']):
            problems.append(f"span {span['id']}: consumer occurrences changed "
                            f"(+{dict(key(actual) - key(span['consumers']))} "
                            f"-{dict(key(span['consumers']) - key(actual))})")
            continue
        span['consumers'] = actual
        changed.append('consumer lines of span ' + span['id'])
    if changed and not problems and not check:
        write_like(SPANS, document, raw)
    return sorted(set(changed)), problems


def refresh_words(check):
    raw = WORDS.read_text(encoding='utf-8')
    document = json.loads(raw)
    changed, problems = [], []
    for routine in document['routines']:
        current = sha_file(routine['source'])
        if current == routine['source_sha256']:
            continue
        committed = subprocess.run(['git', 'show', 'HEAD:' + routine['source']], cwd=ROOT,
                                   capture_output=True).stdout.decode('latin1')
        now = (ROOT / routine['source']).read_bytes().decode('latin1')
        try:
            same = canonical.definition_sha(committed, routine['function']) == \
                canonical.definition_sha(now, routine['function'])
        except Exception as exc:  # renamed or removed routine: a real contract change
            same = False
            problems.append(f"{routine['id']}: cannot compare {routine['function']}: {exc}")
        if not same:
            problems.append(f"{routine['id']}: definition of {routine['function']} changed; review its sites")
            continue
        routine['source_sha256'] = current
        changed.append('word contract ' + routine['id'])
    if changed and not problems and not check:
        write_like(WORDS, document, raw)
    return changed, problems


def main():
    check = '--check' in sys.argv[1:]
    changed, problems = [], []
    for step in (refresh_spans, refresh_words):
        c, p = step(check)
        changed += c
        problems += p
    for line in changed:
        print(('stale: ' if check else 'refreshed: ') + line)
    for line in problems:
        print('CONTRACT CHANGE: ' + line)
    if not changed and not problems:
        print('port pins are current')
    return 1 if problems or (check and changed) else 0


if __name__ == '__main__':
    raise SystemExit(main())
