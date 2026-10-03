"""Previously DOS-verified native lowering of the discarded history overread."""
import hashlib

SOURCE_SHA = '3de9615a57dbe35eacd073726b451478dc5b12396360501631d7553b6139e240'
EVIDENCE = 'portable/tests/history_event_lowering/comparison_report_closure_next10.json'


def adapt(source):
    if hashlib.sha256(source.encode()).hexdigest() != SOURCE_SHA:
        raise ValueError('original S24 source identity changed')
    old = ('_fmemmove(&shownGraphs[i], &shownGraphs[i + 1], (4 - i) * 2);\n'
           '                shownGraphs[3] = (int)0x8000;')
    new = ('/* Native lowering: the one-past read feeds only the slot\n'
           '                 * immediately replaced by the sentinel. */\n'
           '                _fmemmove(&shownGraphs[i], &shownGraphs[i + 1], (3 - i) * 2);\n'
           '                shownGraphs[3] = (int)0x8000;')
    if source.count(old) != 1:
        raise ValueError('history shift/sentinel relation changed')
    return source.replace(old, new), {
        'kind': 'PREVIOUSLY_VERIFIED_NATIVE_HISTORY_OVERREAD_LOWERING',
        'function': 'ToggleHistButton', 'source_sha256': SOURCE_SHA,
        'old_count': '(4 - i) * 2', 'native_count': '(3 - i) * 2',
        'reason': 'Only destination slot 3 loses a copied word; the next statement overwrites it with the same sentinel',
        'prior_dos_native_evidence': EVIDENCE,
        'claim': 'Reuses admitted Next10 lowering; no new DOS comparison or whole-TU behavior claim'}
