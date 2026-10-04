"""Conditional layout-dependence probe in the existing isolated DOS VM.

RAM fixtures only. Never patches objects or accepts a source/storage claim.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from behavior_suites import text_card as suite
import behavior as b

SOURCE = ROOT / 'evidence/behavior/functions/win_PrintStyleTextInRect/contracts/logical-text-v2/module.c'
pair = b.PreparedPair('win_PrintStyleTextInRect', source=SOURCE,
                      out=Path(__file__).parent / 'ctype-vm')
prefix = b.symbol_address('_ctype') + 1 - 35
assert prefix == b.match.DGROUP_SEG*16 + 0x79fc
catalogue = 0x4ee5*16 + 0x500
counter = b.match.DGROUP_SEG*16 + 0x8c24
hotspot = 0x4ee5*16
results = []
for flags in (3, 0):
    case = suite.make_case(f'conditional-DD-prefix-{flags}', bytes([0xdd, 0x78]),
                           (0, 0, 120, 60), styles=((0, 0x100), (1, 0)),
                           record=1, font1=5, font2=5)
    # Synthetic resource name BD matches only after the original DD -> BD
    # signed-prefix uppercase mutation. The next record is a zero sentinel.
    case.writes += [(prefix, bytes([flags])),
                    (catalogue, bytes([0xbd])+bytes(31)+struct.pack('<h',42)+bytes(34))]
    case.observe = [b.Range('hotspot_count', counter, 2),
                    b.Range('first_hotspot', hotspot, 10)]
    result = pair.compare(case)
    assert result.equal, result.diff
    results.append(dict(prefix_flags=flags, equal=result.equal,
        original_ranges=result.original['ranges'], candidate_ranges=result.candidate['ranges'],
        original_draws=result.original['state']['draws'],
        candidate_draws=result.candidate['state']['draws'],
        original_blocks=result.original['blocks'],
        candidate_blocks=result.candidate['blocks']))
assert results[0]['original_ranges']['hotspot_count'] == '0100'
assert results[1]['original_ranges']['hotspot_count'] == '0000'
def pin(path):
    raw = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))
receipt = dict(schema='simant-conditional-ctype-prefix-vm-v35', root_reviewed=True,
    source_or_layout_admitted=False, original_analysis_only=True,
    standalone_source_only_game=False, original_build_bytes_used=0,
    scope='One conditional RAM fixture and a bit-clearing contrast. Actual original '
        'target, font metrics and string helpers execute; only logical draw is modeled '
        'by the existing suite. No shipped-resource reachability, game execution, '
        'heap placement, source acceptance or raster claim.',
    identity=pair.identity,
    whole_tu_peer_claims=list(pair.ctx.claims),
    whole_tu_existing_peers_and_data='PASS (PreparedPair refuses regression)',
    prefix_address=prefix, prefix_relative_to_ctype=-34,
    input_pins=[pin(p) for p in (Path(__file__), SOURCE,
        ROOT/'tools/behavior.py', ROOT/'tools/behavior_suites/text_card.py',
        ROOT/'src/root/m24AB.c', ROOT/'src/root/m25E7.c',
        ROOT/'layout/manifest.json', ROOT/'layout/symbols.json', ROOT/'layout/oracle.lock.json')],
    cases=results,
    conclusion='Strict reconstructed C agrees with the original in both RAM states; '
        'changing only the out-of-owner prefix flag changes hotspot registration. '
        'The algorithm is complete, but prefix memory is relevant to source-only integration.')
Path(__file__).with_name('ctype-prefix-vm.json').write_text(
    json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(status='PASS', counts=[r['original_ranges']['hotspot_count']
                                         for r in results]), indent=2))
