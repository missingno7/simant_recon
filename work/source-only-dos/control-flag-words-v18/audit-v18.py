from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
STRICT_INDEX = ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
SYMBOLS = ROOT / 'layout/symbols.json'
TARGETS = {
    'fd_50F6_0468': (0x0468, 'signed int', 2, 1),
    'fd_50F6_0370': (0x0370, 'signed int', 2, -1),
    'fd_50F6_024E': (0x024E, 'signed int', 2, -1),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(rel: str) -> Path:
    return ROOT / rel.replace('\\', '/')


def main() -> None:
    strict = json.loads(STRICT_INDEX.read_text(encoding='utf-8'))['entries']
    symbols = json.loads(SYMBOLS.read_text(encoding='utf-8'))['data']

    canonical: dict[str, Path] = {}
    for path in (ROOT / 'src').rglob('*'):
        if path.is_file() and path.suffix.lower() in {'.c', '.asm'}:
            source = path.relative_to(ROOT).as_posix()
            canonical[source] = path
    if len(canonical) != 127:
        raise SystemExit(f'expected 127 canonical TUs; saw {len(canonical)}')

    strict_sources: dict[str, Path] = {}
    strict_receipts = []
    for name, entry in strict.items():
        receipt_path = norm(entry['path'])
        if sha(receipt_path) != entry['sha256'] or receipt_path.stat().st_size != entry['size']:
            raise SystemExit(f'strict receipt changed: {entry["path"]}')
        strict_receipts.append({'name': name, 'path': entry['path'],
                                'sha256': sha(receipt_path), 'size': receipt_path.stat().st_size})
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        item = receipt.get('source_override') if name == 'DrawBalloons' else receipt['registered_source']
        if not item:
            raise SystemExit('DrawBalloons effective source override is missing')
        rel = item['path'].replace('\\', '/')
        path = norm(rel)
        if sha(path) != item['sha256']:
            raise SystemExit(f'strict source hash changed: {rel}')
        strict_sources[rel] = path
    if len(strict_sources) != 29:
        raise SystemExit(f'expected 29 effective strict sources; saw {len(strict_sources)}')

    sources = {**canonical, **strict_sources}
    draw_receipt = json.loads(norm(strict['DrawBalloons']['path']).read_text(encoding='utf-8'))
    correction = draw_receipt['source_override']['path'].replace('\\', '/')

    aliases = []
    for name, entry in symbols.items():
        if entry.get('seg') != 0x50F6:
            continue
        off = entry.get('off', -1)
        for target, (base, _, size, _) in TARGETS.items():
            if base <= off < base + size:
                aliases.append({'name': name, 'offset': off, 'target': target,
                                'interior': off != base,
                                'alias_of': entry.get('alias_of'),
                                'grounding': entry.get('grounding')})

    names = set(TARGETS) | {row['name'] for row in aliases}
    name_re = re.compile(r'(?<![A-Za-z0-9_])(?:' + '|'.join(
        re.escape(n) for n in sorted(names, key=len, reverse=True)
    ) + r')(?![A-Za-z0-9_])')
    offset_values = sorted({off for base, _, size, _ in TARGETS.values()
                            for off in range(base, base + size)})
    offsets = sorted({f'{off:04X}' for off in offset_values})
    decimal_offsets = sorted({str(off) for off in offset_values})
    # Keep syntactic candidates rather than treating a matching number as a use.
    numeric_re = re.compile(r'(?i)(?<![A-Za-z0-9_])(?:0x)?(?:' + '|'.join(offsets) + r')(?:h)?(?![A-Za-z0-9_])')
    decimal_re = re.compile(r'(?<![A-Za-z0-9_])(?:' + '|'.join(decimal_offsets) + r')(?![A-Za-z0-9_])')
    addr_re = re.compile(r'(?i)(?:0x)?50f6h?\s*:\s*(?:0x)?(?:' + '|'.join(offsets) + r')h?')
    segment_re = re.compile(r'(?i)(?<![A-Za-z0-9_])(?:0x50f6|50f6h)(?![A-Za-z0-9_])')
    computed_re = re.compile(r'(?i)\b(?:MK_FP|FP_SEG|FP_OFF|ES\s*:)\b')
    name_hits, numeric_hits, asm_numeric, computed_candidates = [], [], [], []
    for rel, path in sorted(sources.items()):
        text = path.read_text(encoding='latin1')
        for line_no, line in enumerate(text.splitlines(), 1):
            found = sorted(set(name_re.findall(line)))
            if found:
                row = {'source': rel, 'line': line_no, 'names': found, 'text': line.strip()[:300]}
                name_hits.append(row)
            numbers = numeric_re.findall(line)
            full = addr_re.findall(line)
            decimal = decimal_re.findall(line)
            segment = segment_re.findall(line)
            computed = bool(computed_re.search(line))
            if numbers or decimal or full or segment:
                row = {'source': rel, 'line': line_no,
                       'offset_literals': sorted(set(v.upper().removeprefix('0X').removesuffix('H') for v in numbers)),
                       'decimal_offset_literals': sorted(set(decimal)),
                       'segment_literals': sorted(set(segment)),
                       'segment_offset_spellings': sorted(set(v.upper() for v in full)),
                       'text': line.strip()[:300]}
                numeric_hits.append(row)
                if path.suffix.lower() == '.asm':
                    asm_numeric.append(row)
                if computed or full or (segment and (numbers or decimal)):
                    computed_candidates.append(row)

    save_rows = []
    save_source = ROOT / 'src/S09/m35F5.c'
    save_re = re.compile(r'^\s*\{\s*2\s*,\s*1\s*,\s*\(void far \*\)&(fd_50F6_(?:0468|0370|024E))\s*\}')
    for line_no, line in enumerate(save_source.read_text(encoding='latin1').splitlines(), 1):
        m = save_re.search(line)
        if m:
            save_rows.append({'name': m.group(1), 'line': line_no, 'text': line.strip()})

    for name, (off, typ, extent, init) in TARGETS.items():
        symbol = symbols.get(name)
        if not symbol or symbol.get('seg') != 0x50F6 or symbol.get('off') != off:
            raise SystemExit(f'registry mismatch: {name}')

    input_paths = [STRICT_INDEX, SYMBOLS]
    result = {
        'schema': 'dos-control-flag-words-source-owner-review-v1',
        'root_claimed': False,
        'admitted': False,
        'scope': 'exactly fd_50F6_0468, fd_50F6_0370, fd_50F6_024E; bounded independent source inventory',
        'inventory': {
            'canonical_translation_units': len(canonical),
            'canonical_c': sum(p.suffix.lower() == '.c' for p in canonical.values()),
            'canonical_asm': sum(p.suffix.lower() == '.asm' for p in canonical.values()),
            'effective_strict_sources': len(strict_sources),
            'draw_balloons_reviewed_correction': correction,
            'combined_distinct_source_files': len(sources),
            'original_game_executable_or_object_read': False,
            'source_hashes': [{'path': rel, 'sha256': sha(p)} for rel, p in sorted(sources.items())],
        },
        'evidence_hashes': [{'path': str(p.relative_to(ROOT)).replace('\\', '/'), 'sha256': sha(p)} for p in input_paths],
        'strict_receipt_pins': sorted(strict_receipts, key=lambda row: row['name']),
        'targets': TARGETS,
        'registered_aliases_and_interiors': aliases,
        'named_source_references': name_hits,
        'numeric_address_candidates': numeric_hits,
        'assembly_numeric_candidates': asm_numeric,
        'computed_address_candidates': computed_candidates,
        'save_rows': save_rows,
        'indirect_save_restore_consumers': [
            {'source': 'src/S09/m35F5.c', 'function': 'LoadGame', 'line': 118,
             'operation': 'read(fd, p->data, p->count * p->size)'},
            {'source': 'src/S09/m35F5.c', 'function': 'SaveGame (o09_35F5_0188)', 'line': 183,
             'operation': 'write(fd, p->data, p->count * p->size)'},
        ],
        'build_report_used_as_authority': False,
        'source_owner_assessment': {
            'typed_source_extent_and_initialization_closed': True,
            'source_owned_storage_candidate': 'work/source-only-dos/control-flag-words-v18/provider.c',
            'runtime_save_restore_byte_interface_closed': True,
            'flag_meaning_and_init_restore_lifecycle_closed': False,
            'historical_object_ownership_or_placement_closed': False,
            'basis': [
                'root:0798 declares all three as signed 16-bit int far and initControls stores +1, -1, -1 at the registered ES: offsets.',
                'S09:35F5 has size=2/count=1 table rows for each address; LoadGame passes p->data and p->count*p->size to read, while SaveGame passes them to write.',
                'The inventory found no other named/registered-interior source reference and no assembly/direct-numeric or computed-address source candidate.',
                'This closes the natural three-word zero-filled storage candidate and generic two-byte save/restore interface; flag meaning, init-versus-restore scheduling, downstream uses outside this source graph, and historical COMDEF/object ownership remain unproven.',
            ],
        },
        'review_limits': [
            'No segment-gap, neighboring-symbol, source-order, or original-TU-extent sizing was used.',
            'Numeric literals are surfaced as candidates, not promoted to references without an address expression/context.',
            'The scan inventories the 127 canonical TU paths, 29 receipt-verified effective strict sources, and the reviewed DrawBalloons correction; it does not prove all runtime paths execute initControls before saved-state restoration or establish what other runtime components do with the words.',
            'Any unregistered computed pointer arithmetic whose source expression contains no target name/address spelling remains outside static text evidence.',
        ],
        'audit_tool': {'path': str(Path(__file__).relative_to(ROOT)).replace('\\', '/'),
                       'sha256': sha(Path(__file__))},
    }
    (OUT / 'audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"canonical={len(canonical)} strict={len(strict_sources)} files={len(sources)} names={len(name_hits)} numeric={len(numeric_hits)} asm_numeric={len(asm_numeric)} aliases={len(aliases)} save_rows={len(save_rows)}")
    for row in name_hits:
        print(f"{row['source']}:{row['line']}: {','.join(row['names'])}: {row['text']}")
    for row in numeric_hits:
        print(f"NUM {row['source']}:{row['line']}: {row['text']}")


if __name__ == '__main__':
    main()
