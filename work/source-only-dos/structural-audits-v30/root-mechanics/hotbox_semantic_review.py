"""Record root static interpretation without admitting the unregistered object."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'work/source-only-dos/structural-audits-v30/hotbox/root-semantic-review.json'

def pin(path):
    return dict(path=path.relative_to(ROOT).as_posix(),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=path.stat().st_size)

def main():
    candidate = ROOT / 'work/source-only-dos/structural-audits-v29/hotbox-v35/receipt.json'
    packet = json.loads(candidate.read_bytes())
    # Reopen each named source/evidence input, preserving the worker packet.
    pins = []
    def walk(value):
        if isinstance(value, dict):
            if 'path' in value and 'sha256' in value:
                path = ROOT / value['path']
                assert pin(path)['sha256'] == value['sha256'], value['path']
                pins.append(pin(path))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(packet)
    fields = [dict(offset=2*i, width=2, meaning=name) for i, name in enumerate(
        ('left: signed inclusive x', 'top: signed inclusive y',
         'right: signed inclusive x', 'bottom: signed inclusive y',
         'callback far offset', 'callback far segment',
         'callback payload code / list key', 'callback payload xE',
         'packed mouse event mask: any-bit match'))]
    review = dict(schema='simant-root-hotbox-semantic-review-v30',
        root_reviewed=True, production_admission=False, debt_discharged_bytes=0,
        span='dgroup_60b0', size=18,
        historical_classification='UNREFERENCED_TIMER_COMPATIBLE_RECORD_WITH_REAL_RELOCATION',
        current_classification='EVENT_REGION_RECORD_WITH_UNPROVEN_REGISTRATION_AND_SOURCE_INSTANCE',
        fields=fields,
        static_anchors=[
            dict(source='src/root/m1B73.asm', functions=['f_1B73_0AC3', 'f_1B73_0B00'],
                 fact='Both list insertion paths copy nine words; walking increments by 0x12.'),
            dict(source='src/root/m1B73.asm', functions=['f_1B73_0CEF'],
                 fact='Signed inclusive rectangle comparisons, mask TEST at +16, indirect callback at +8, arguments +12/+14/event/x/y, AX zero ends scan.'),
            dict(source='src/root/m1B73.asm', functions=['f_1B73_030F', 'f_1B73_036E'],
                 fact='The recorded callback enqueues payload/event/coordinates and explicitly returns AX=0.'),
            dict(source='src/root/m1FD2.c', functions=['f_1FD2_044F'],
                 fact='g_603A is independently registered through the same API; its mask differs, so it is no alias or registration proof for 60B0.')],
        worker_receipt=pin(candidate), reopened_inputs=pins,
        unexplained_field_bytes=0,
        remaining=['No proven source-instance owner or containing contribution.',
                   'No inbound registration/use chain; static no-reference scans do not exclude computed pointers.',
                   'No provider, placement, lifetime or harmless/dead-data conclusion admitted.'],
        build_or_execution='NONE')
    assert not OUT.exists()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes((json.dumps(review, indent=2)+'\n').encode())
    print('ROOT HOTBOX SEMANTIC REVIEW PASS:', len(pins), 'input pins; zero bytes discharged')

if __name__ == '__main__':
    main()
