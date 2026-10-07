"""Named exclusions authorized for the differential observation domain.

Snapshot files always preserve the original bytes. No policy writes source state.
"""
G5702_STACK_RESIDUE_TAIL = {
    'id': 'G5702_STACK_RESIDUE_TAIL',
    'symbol': 'g_5702',
    'source': 'src/root/m1E57.c:f_1E57_00B1',
    'reason': 'buf[32] is filled only through the 0x8000 terminator, then '
              '_fmemcpy(g_5702, buf, sizeof(buf)) stores its uninitialized stack tail. '
              'DOS/native stack residue beyond a shared first sentinel is excluded '
              'by the reviewed comparison policy; prefix and sentinel remain compared.',
    'scope': '64-byte int16 list; exclude bytes strictly after the shared first '
             '0x8000 word. Different or missing sentinel positions disable exclusion.',
}


def state_prefix(name, dos, native, raw_state=False):
    """Return comparable bytes and an explicit receipt, never a silent mask."""
    if name != 'g_5702' or raw_state:
        return dos, native, None
    receipt = dict(G5702_STACK_RESIDUE_TAIL, applied=False)
    if len(dos) != 64 or len(native) != 64:
        receipt['status'] = 'NOT_APPLIED_EXTENT'
        return dos, native, receipt
    def sentinel(data):
        return next((i for i in range(0, 64, 2) if data[i:i+2] == b'\x00\x80'), None)
    left, right = sentinel(dos), sentinel(native)
    receipt['sentinel_offsets'] = [left, right]
    if left is None or left != right:
        receipt['status'] = 'NOT_APPLIED_SENTINEL_MISMATCH'
        return dos, native, receipt
    start = left + 2
    receipt.update(status='EXCLUDED_STACK_RESIDUE_TAIL', applied=True,
                   compared_range=[0, start], excluded_range=[start, 64],
                   excluded_bytes=64-start,
                   excluded_differing_offsets=[i for i in range(start, 64) if dos[i] != native[i]])
    return dos[:start], native[:start], receipt
