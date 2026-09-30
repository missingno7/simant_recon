"""Shared module context for the analysis helpers (slots.py, records.py, variants.py, idscan.py).

Not a gate and never a writer of canonical state: it only *reads* layout/manifest.json,
layout/functions.json and layout/symbols.json, compiles through tools/compiler.py and binds
through tools/match.py / tools/modules.py.  Everything a helper writes goes under build/.

    ctx = modctx.resolve(module="root:1383")                      # canonical source + manifest options
    ctx = modctx.resolve(source="build/workers/me/m1383.c")       # module inferred from the functions
    ctx = modctx.resolve(func="DoAntMoveY", source="draft.c",     # module of a function
                         flags=["/AL", "/Os", "/Oe", "/Og", "/Zi"])

Options resolve in this order: explicit argument, the module's manifest record, the profile
defaults (``functions.DEFAULT_PROFILE``).  Module keys may arrive as ``root;1383`` from Git
Bash (path-list conversion); ``modules.parse_key`` undoes that.  Arguments that Git Bash turned
into Windows paths (``/AL`` -> ``C:/Program Files/Git/AL``) are refused, never guessed back.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compiler  # noqa: E402
import exe as exemod  # noqa: E402
import functions as fnmod  # noqa: E402
import match  # noqa: E402
import modules as modmod  # noqa: E402
from omf import OmfReader  # noqa: E402

ROOT = exemod.ROOT
BUILD = ROOT / "build"
# what Git Bash makes of "/AL": the MSYS root (Git for Windows or MSYS2) prefixed
MANGLED_RE = re.compile(r"^[A-Za-z]:[/\\](?:Program Files[/\\]Git|Git|msys64|msys32)(?:[/\\]|$)", re.I)


class HelperError(SystemExit):
    """A usage error: the message is printed and the helper exits with status 1."""

    def __init__(self, msg: str):
        super().__init__(f"error: {msg}")


def check_arg(value: str, what: str) -> str:
    """Refuse an argument that Git Bash rewrote into a Windows path."""
    if MANGLED_RE.match(value or ""):
        raise HelperError(f"{what} {value!r} looks rewritten by MSYS path conversion; "
                          "set MSYS_NO_PATHCONV=1 (and MSYS2_ARG_CONV_EXCL='*')")
    return value


def parse_placements(specs) -> dict:
    """``SEG=SSSS:OOOO[:SIZE]`` (hex frame, hex offset, decimal size) -> {name: {seg, off[, size]}}.
    ``;`` is accepted for ``:`` (Git Bash path-list conversion)."""
    out = {}
    for spec in specs or []:
        check_arg(spec, "--placement")
        name, sep, addr = spec.partition("=")
        parts = addr.replace(";", ":").split(":")
        if not sep or len(parts) not in (2, 3):
            raise HelperError(f"bad placement {spec!r} (expected SEG=SSSS:OOOO[:SIZE])")
        p = {"seg": int(parts[0], 16), "off": int(parts[1], 16)}
        if len(parts) == 3:
            p["size"] = int(parts[2])
        out[name] = p
    return out


def under_build(path: Path) -> Path:
    """Scratch output must live under build/."""
    p = Path(path).resolve()
    try:
        p.relative_to(BUILD.resolve())
    except ValueError:
        raise HelperError(f"output {p} is not under {BUILD}") from None
    return p


def scratch(tool: str, *parts: str) -> Path:
    d = BUILD / "helpers" / tool
    for part in parts:
        d = d / part
    d.mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class Ctx:
    key: str
    unit: str
    seg: int
    origin: int | None
    profile: str
    flags: list
    placements: dict                      # name -> {seg, off[, size]} (manifest + overrides)
    lang: str = "c"
    extent: dict | None = None
    claims: list = field(default_factory=list)      # manifest claims (may be empty)
    functions: list = field(default_factory=list)   # function-table rows of this object, frame order
    source: Path | None = None
    text: str = ""
    in_manifest: bool = False

    @property
    def placements_bind(self) -> dict:
        return {k: {"seg": v["seg"], "off": v["off"]} for k, v in self.placements.items()}

    def module_dict(self, extent: bool = True) -> dict:
        """The module record ``modules.verify_module`` expects."""
        m = {"unit": self.unit, "seg": self.seg, "profile": self.profile, "flags": list(self.flags),
             "placements": dict(self.placements), "lang": self.lang}
        if self.origin is not None:
            m["origin"] = self.origin
        if extent and self.extent:
            m["extent"] = dict(self.extent)
        return m

    def function(self, name: str) -> dict:
        for r in self.functions:
            if r["name"] == name:
                return r
        f = fnmod.get(name)
        if f["unit"] != self.unit or f["seg"] != self.seg:
            raise HelperError(f"{name} is not in module {self.key}")
        return f

    @property
    def span(self) -> tuple[int, int]:
        """[lo, hi) frame offsets of this object's code: the extent if known, else the
        function-table rows of the object."""
        if self.extent:
            return self.extent["start"] - self.seg * 16, self.extent["end"] - self.seg * 16
        if not self.functions:
            raise HelperError(f"module {self.key} has no function-table rows")
        return self.functions[0]["off"], max(r["off"] + r["size"] for r in self.functions)


def module_rows(unit: str, seg: int, origin: int | None, man: dict | None = None) -> list:
    man = man or modmod.load_manifest()
    lo, hi = modmod.object_range(man, unit, seg, origin)
    rows = [dict(r, name=fnmod.name_of(unit, seg, r["off"])) for r in fnmod.table()["functions"]
            if r["unit"] == unit and r["seg"] == seg and lo <= r["off"] < hi]
    return sorted(rows, key=lambda r: r["off"])


def key_for_function(f: dict, man: dict | None = None) -> str:
    """Module key of the object that owns function row ``f`` (``UNIT:SEG`` or ``UNIT:SEG@OFF``)."""
    man = man or modmod.load_manifest()
    best = None
    for k, m in man["modules"].items():
        if m["unit"] == f["unit"] and m["seg"] == f["seg"]:
            lo, hi = modmod.object_range(man, m["unit"], m["seg"], m.get("origin"))
            if lo <= f["off"] < hi:
                best = k
    return best or modmod.module_key(f["unit"], f["seg"])


def infer_module(text: str) -> str:
    """Module key from the function definitions of a draft: every defined, registered function
    outside the SCAFFOLD block votes with its unit:seg; the majority wins."""
    defs = set(modmod.FUNC_DEF_RE.findall(modmod.SCAFFOLD_RE.sub("", text)))
    votes: dict = {}
    for name in defs:
        try:
            f = fnmod.get(name)
        except SystemExit:
            continue
        k = key_for_function(f)
        votes[k] = votes.get(k, 0) + 1
    if not votes:
        raise HelperError("cannot infer the module from the source (no registered function defined); "
                          "pass --module UNIT:SEG")
    return max(votes.items(), key=lambda kv: kv[1])[0]


def resolve(module: str | None = None, source: str | Path | None = None, func: str | None = None,
            profile: str | None = None, flags=None, placements=None, target: str | None = None) -> Ctx:
    """Build the context.  ``target`` is a convenience for ``MODULE_OR_SOURCE`` positionals: a
    module key (``root:1383``, ``root;1383``) or a source path."""
    if target:
        check_arg(target, "target")
        if modmod.KEY_RE.match(target.strip()) and not Path(target).exists():
            module = module or target
        else:
            source = source or target
    if module:
        check_arg(module, "--module")
    if flags:
        flags = [check_arg(f, "flag") for f in flags]
        try:
            compiler.check_flags(list(flags))
        except compiler.CompileError as e:
            raise HelperError(str(e)) from None
    text = ""
    if source is not None:
        source = Path(check_arg(str(source), "source"))
        if not source.exists():
            raise HelperError(f"no such source {source}")
        text = source.read_text(encoding="latin1")
    man = modmod.load_manifest()
    if module is None and func is not None:
        module = key_for_function(fnmod.get(func), man)
    if module is None and text:
        module = infer_module(text)
    if module is None:
        raise HelperError("need a module key, a function or a source")
    unit, seg, origin = modmod.parse_key(module)
    key = modmod.module_key(unit, seg, origin)
    rec = man["modules"].get(key)
    lang = "asm" if (source is not None and source.suffix.lower() == ".asm") else (rec or {}).get("lang", "c")
    if source is None:
        if rec is None:
            raise HelperError(f"module {key} has no canonical source; pass a draft")
        source = ROOT / rec["source"]
        text = source.read_text(encoding="latin1")
    prof = profile or (rec["profile"] if rec else ("masm510" if lang == "asm" else fnmod.DEFAULT_PROFILE))
    fl = list(flags) if flags else (list(rec["flags"]) if rec else fnmod.profile_flags(prof))
    pl = dict((rec or {}).get("placements", {}))
    pl.update(parse_placements(placements))
    return Ctx(key=key, unit=unit, seg=seg, origin=origin, profile=prof, flags=fl, placements=pl, lang=lang,
               extent=(rec or {}).get("extent"), claims=list((rec or {}).get("claims", [])),
               functions=module_rows(unit, seg, origin, man), source=source, text=text,
               in_manifest=rec is not None)


def compile_text(ctx: Ctx, text: str | None = None, extra_flags=(), keep: bool = False) -> compiler.Result:
    text = ctx.text if text is None else text
    if ctx.lang == "asm":
        return compiler.assemble(text, ctx.profile, list(ctx.flags) + list(extra_flags), keep=keep)
    return compiler.compile_c(text, ctx.profile, list(ctx.flags) + list(extra_flags), keep=keep)


def read_obj(obj_bytes: bytes):
    return OmfReader(communals=True).read(obj_bytes)


def claim_for(row: dict) -> dict:
    """A claim record for an (unclaimed) function-table row, so ``modules.verify_module`` can
    check it exactly like a manifest claim.  Nothing is written anywhere."""
    x = exemod.load()
    orig = x.read(row["unit"], row["seg"] * 16 + row["off"], row["size"])
    return {"name": row["name"], "unit": row["unit"], "seg": row["seg"], "off": row["off"],
            "size": row["size"], "target_sha256": hashlib.sha256(orig).hexdigest(), "kind": "C"}


def bind_function(ctx: Ctx, obj, row: dict):
    """(MatchResult or None, public record or None) for one function of the module, bound with
    ``match.Binder`` under the context's placements (the same binding as search.py)."""
    pub, prec = match.public_in(obj, row["name"])
    if prec is None:
        return None, None
    t = match.Target(row["unit"], row["seg"], row["off"], row["size"])
    return match.Binder(t, obj, prec["segment"], pub, ctx.placements_bind).bind(), prec


class FrameMap:
    """Piecewise object-offset -> frame-offset map of one code segment: every candidate public
    that is a function of the module contributes the shift ``frame_off - obj_off`` from its
    public onwards.  ``exact_len[name]`` says whether the candidate function has the original
    length (only then do inner offsets correspond)."""

    def __init__(self, ctx: Ctx, obj, segment: str | None = None):
        self.anchors = []            # (obj_off, frame_off, name, cand_len, target_len)
        by_name = {r["name"]: r for r in ctx.functions}
        pubs = []
        for p in obj.publics + getattr(obj, "local_publics", []):
            n = match.c_name(p["name"])
            if n in by_name and (segment is None or p["segment"] == segment):
                pubs.append((p["offset"], n, p["segment"]))
        if segment is None and pubs:
            segs = {}
            for _, _, s in pubs:
                segs[s] = segs.get(s, 0) + 1
            segment = max(segs.items(), key=lambda kv: kv[1])[0]
            pubs = [p for p in pubs if p[2] == segment]
        self.segment = segment
        pubs.sort()
        all_offs = sorted(p["offset"] for p in obj.publics + getattr(obj, "local_publics", [])
                          if p["segment"] == segment)
        seglen = len(obj.segments.get(segment, b"")) if segment else 0
        for o, n, _ in pubs:
            nxt = min((q for q in all_offs if q > o), default=seglen)
            self.anchors.append((o, by_name[n]["off"], n, nxt - o, by_name[n]["size"]))
        self.exact_len = {n: cl == tl or (cl == tl + 1) for _, _, n, cl, tl in self.anchors}

    def to_frame(self, o: int) -> int | None:
        best = None
        for ao, fo, *_ in self.anchors:
            if ao <= o:
                best = (ao, fo)
        return None if best is None else o - best[0] + best[1]

    def to_obj(self, f: int) -> int | None:
        best = None
        for ao, fo, *_ in self.anchors:
            if fo <= f and (best is None or fo >= best[1]):
                best = (ao, fo)
        return None if best is None else f - best[1] + best[0]

    def func_at_obj(self, o: int) -> str | None:
        best = None
        for ao, _, n, *_ in self.anchors:
            if ao <= o:
                best = n
        return best


def code_segment_index(obj, segment: str) -> int | None:
    for sd in obj.segment_defs:
        if sd["name"] == segment:
            return sd["index"]
    return None


def status_char(r: dict | None) -> str:
    """One character per claim in compact tables: E exact, r exact bytes but within-group
    relocation order pending (partial module), S claimed name inside SCAFFOLD, - absent,
    . mismatch."""
    if r is None:
        return "-"
    if r.get("exact"):
        return "r" if r.get("reloc_order") == "WITHIN_GROUP_PENDING" else "E"
    reasons = " ".join(r.get("reasons", []))
    if "SCAFFOLD" in reasons:
        return "S"
    if reasons.startswith("no public"):
        return "-"
    return "."


def dumps(obj) -> str:
    return json.dumps(obj, indent=1, default=str)
