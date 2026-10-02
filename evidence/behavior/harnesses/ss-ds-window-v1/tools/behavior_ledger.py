#!/usr/bin/env python3
"""Append-only per-case audit ledger for original-vs-candidate behavior runs."""
from __future__ import annotations

import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite float in behavioral input/observation")
        return value
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if isinstance(value, (tuple, list)):
        return [_json_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_value(value[k]) for k in sorted(value, key=lambda x: str(x))}
    raise TypeError(f"unsupported behavioral ledger value: {type(value).__name__}")


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(_json_value(value), sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _callable_id(value: Any) -> str | None:
    if value is None:
        return None
    return f"{getattr(value, '__module__', type(value).__module__)}.{getattr(value, '__qualname__', type(value).__qualname__)}"


def _case_input(case: Any) -> dict:
    callbacks = {}
    for name, spec in sorted(case.callbacks.items()):
        callbacks[name] = {
            "stack_words": spec.stack_words,
            "handler": _callable_id(spec.handler),
            "register_args": list(spec.register_args),
            "pop": spec.pop,
            "project": _callable_id(spec.project),
        }
    io_reads = {}
    for port, provider in sorted(case.io_reads.items()):
        io_reads[str(port)] = _callable_id(provider) if callable(provider) else provider
    return _json_value({
        "label": case.label, "args": case.args,
        "writes": [(address, bytes(data)) for address, data in case.writes],
        "observe": [{"name": r.name, "address": r.address, "size": r.size} for r in case.observe],
        "callbacks": callbacks, "return_kind": case.return_kind,
        "registers": case.registers, "state": case.state,
        "metadata": case.metadata, "io_reads": io_reads,
        "max_instructions": case.max_instructions, "max_blocks": case.max_blocks,
        "observe_at_calls": case.observe_at_calls, "callee_pop": case.callee_pop,
        "stack_bytes": case.stack_bytes,
    })


def _final_memory_snapshot(machine, addresses: set[int]) -> list[tuple[int, int]]:
    # PreparedPair already filters the actual per-case stack interval. Do not
    # drop a fixed address range: it may contain heap or globals in this case.
    return [(address, machine.read(address, 1)[0]) for address in sorted(addresses)]


def _observation(result: dict, memory: list[tuple[int, int]]) -> dict:
    # Deliberately exclude block counts, raw_trace, and write-history addresses by
    # themselves. Final bytes in the union of writes remain part of the contract.
    fields = ("return", "ranges", "trace", "io", "state", "preserved_registers")
    return {**{key: result[key] for key in fields},
            "final_union_nonstack_memory": memory}


class CaseLedger:
    """Write truthful per-case records after PreparedPair.compare has executed.

    Use a `.jsonl.gz` output for large randomized campaigns. `finalize()` returns
    the report pin only after closing the stream; no counts can be entered manually.
    """

    def __init__(self, path: Path | str, pair: Any, compared_effects: list[str]):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not compared_effects or any(not isinstance(x, str) or not x for x in compared_effects):
            raise ValueError("compared_effects must be a non-empty list")
        self.compared_effects = list(dict.fromkeys(compared_effects))
        self.identity = _json_value(pair.identity)
        required_identity = ("function", "source_sha256", "object_sha256", "oracle_sha256",
                             "harness_sha256", "manifest_sha256")
        missing = [key for key in required_identity if not self.identity.get(key)]
        if missing:
            raise ValueError(f"pair identity lacks required pins: {missing}")
        self.pair = pair
        self._ids: set[str] = set()
        self._lane_counts = {"directed": 0, "randomized": 0}
        self._closed = False
        if self.path.name.endswith(".gz"):
            self._raw = self.path.open("wb")
            self._stream = gzip.GzipFile(fileobj=self._raw, mode="wb", filename="", mtime=0)
            import io
            self._text = io.TextIOWrapper(self._stream, encoding="utf-8", newline="\n")
        else:
            self._raw = None
            self._stream = None
            self._text = self.path.open("w", encoding="utf-8", newline="\n")

    def record(self, case: Any, result: Any, *, lane: str,
               compared_effects: list[str] | None = None) -> dict:
        if self._closed:
            raise RuntimeError("case ledger is already finalized")
        if lane not in self._lane_counts:
            raise ValueError("lane must be directed or randomized")
        case_id = case.label
        if not isinstance(case_id, str) or not case_id or case_id in self._ids:
            raise ValueError("case label must be non-empty and unique within the ledger")
        if not hasattr(result, "original") or not hasattr(result, "candidate"):
            raise ValueError("record requires a completed PreparedPair.compare result")
        if not hasattr(self.pair, "original_machine") or not hasattr(self.pair, "candidate_machine"):
            raise ValueError("pair does not expose the two execution machines")
        effects = list(dict.fromkeys(compared_effects or self.compared_effects))
        if not set(self.compared_effects).issubset(effects):
            raise ValueError("case effects omit a required contract effect")
        original_writes = set(result.original.get("written_addresses", []))
        candidate_writes = set(result.candidate.get("written_addresses", []))
        union = original_writes | candidate_writes
        original_memory = _final_memory_snapshot(self.pair.original_machine, union)
        candidate_memory = _final_memory_snapshot(self.pair.candidate_machine, union)
        original_observation = _observation(result.original, original_memory)
        candidate_observation = _observation(result.candidate, candidate_memory)
        original_hash = canonical_hash(original_observation)
        candidate_hash = canonical_hash(candidate_observation)
        equal = bool(result.equal) and original_hash == candidate_hash
        row = {
            "case_id": case_id, "lane": lane,
            "input_sha256": canonical_hash(_case_input(case)),
            "original_executed": True, "candidate_executed": True,
            "equal": equal,
            "compared_effects": effects,
            "original_observation_sha256": original_hash,
            "candidate_observation_sha256": candidate_hash,
            "function": self.identity["function"],
            "oracle_sha256": self.identity["oracle_sha256"],
        }
        if not equal:
            row["difference"] = _json_value(getattr(result, "diff", {}))
        self._text.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
        self._ids.add(case_id)
        self._lane_counts[lane] += 1
        return row

    def finalize(self) -> dict:
        if not self._closed:
            self._text.flush()
            self._text.close()
            if self._raw:
                self._raw.close()
            self._closed = True
        return {
            "schema": "behavior-case-ledger-v1",
            "path": self.path.as_posix(),
            "sha256": _file_hash(self.path),
            "row_count": len(self._ids),
            "lane_counts": dict(self._lane_counts),
            "identity": self.identity,
            "compression": "gzip" if self.path.name.endswith(".gz") else "none",
        }

    close = finalize


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()
