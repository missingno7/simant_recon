"""Read-only COFF section/relocation comparison for native whole-TU controls."""
from pathlib import Path
import hashlib
import struct


def sections(path):
    raw = Path(path).read_bytes()
    _, count, _, symbol_offset, symbol_count, optional_size, _ = struct.unpack_from("<HHLLLHH", raw)
    string_offset = symbol_offset + symbol_count * 18
    strings = raw[string_offset:]

    def name(field):
        if field.startswith(b"/"):
            offset = int(field[1:].rstrip(b"\0"))
            return strings[offset:].split(b"\0", 1)[0].decode("ascii")
        if field[:4] == b"\0" * 4:
            offset = struct.unpack_from("<L", field, 4)[0]
            return strings[offset:].split(b"\0", 1)[0].decode("ascii")
        return field.rstrip(b"\0").decode("ascii")

    headers = []
    for i in range(count):
        item = struct.unpack_from("<8sLLLLLLHHL", raw, 20 + optional_size + i * 40)
        headers.append((name(item[0]), item))
    symbols = {}
    index = 0
    while index < symbol_count:
        field, value, section, kind, storage, aux = struct.unpack_from("<8sLhHBB", raw, symbol_offset + index * 18)
        symbols[index] = (name(field), value, headers[section - 1][0] if section > 0 else section, kind, storage)
        index += 1 + aux
    result = {}
    for section_name, item in headers:
        _, virtual_size, _, size, start, rel_start, _, rel_count, _, flags = item
        relocations = []
        for i in range(rel_count):
            at, symbol_index, kind = struct.unpack_from("<LLH", raw, rel_start + i * 10)
            relocations.append((at, symbols[symbol_index], kind))
        result[section_name] = {"bytes": raw[start:start + size] if start else b"", "virtual_size": virtual_size,
                                "flags": flags, "relocations": relocations}
    return result


def compare(old, new, target="win_DoProxMenu"):
    a, b = sections(old), sections(new)
    if a.keys() != b.keys():
        raise AssertionError("whole-TU section inventory changed")
    code = [n for n in a if n.startswith(".text$")]
    peers = [n for n in code if n != ".text$" + target]
    if any(a[n] != b[n] for n in peers):
        raise AssertionError("peer function code or symbolic relocation changed")
    storage = [n for n in a if not n.startswith((".text", ".debug", ".xdata", ".pdata"))]
    if any(a[n] != b[n] for n in storage):
        raise AssertionError("whole-TU storage section or symbolic relocation changed")
    return {"whole_tu_functions": len(code), "unchanged_peer_functions": len(peers),
            "changed_function": target, "target_code_changed": a[".text$" + target] != b[".text$" + target],
            "unchanged_storage_sections": storage,
            "peer_section_sha256": {n: hashlib.sha256(a[n]["bytes"]).hexdigest() for n in peers},
            "method": "Read-only COFF function-section bytes, flags, virtual size and full symbolic relocation targets/types/offsets. Storage sections use the same full comparison. Debug source paths are metadata and are not game code or storage."}
