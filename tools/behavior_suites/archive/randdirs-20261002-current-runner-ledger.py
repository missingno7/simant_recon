"""GetMyRandDirs controlled inputs and strict external-helper fixtures.

This module deliberately does not claim oracle equivalence by itself.  The
fixtures model the documented contracts of GetDis/GetDir/TileCanBeMovedOn;
the original DOS function still has to be invoked by the common Unicorn16
runner with the same fixtures before any behavioral status can be recorded.

Usage as a generator:
    python tools/behavior_suites/randdirs.py --count 100000 --seed 0x1686

The JSONL scenarios can be consumed by the DOS and reconstructed-code adapters.
Each scenario includes all helper inputs and the expected helper call trace for
the source-level model. Unexpected helper calls or accesses are errors.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass, replace
from typing import Any, Iterable


FUNCTION = "o25_3BA4_1686"
DOS_FUNCTION = "S25:3BA4:1686"
ORACLE_HELPERS = ("f_0BE8_0B83", "f_0BE8_0B21", "TileCanBeMovedOn")

# GetDir's documented directions are clockwise from north.  The historical
# direction arrays are loaded by the runner, and checked against these values
# before cases execute; this copy only defines deterministic fixture inputs.
DX8 = (0, 1, 1, 1, 0, -1, -1, -1)
DY8 = (-1, -1, 0, 1, 1, 1, 0, -1)


@dataclass(frozen=True)
class Scenario:
    case_id: str
    plane: int
    x: int
    y: int
    a: int
    b: int
    rot: int
    direction: int
    mode: int
    from_plane: int
    from_x: int
    from_y: int
    previous_x: int
    previous_y: int
    # One bit per direction.  It means the tile helper returns nonzero for
    # exactly that direction when that neighbor is queried.
    movable_mask: int
    seed_group: str

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["movable_mask"] = f"0x{self.movable_mask:02x}"
        d["expected_helpers"] = helper_fixture(self).description()
        return d


@dataclass
class HelperTrace:
    distance_calls: list[tuple[int, int, int, int]]
    direction_calls: list[tuple[int, int, int, int]]
    move_queries: list[tuple[int, int, int, int, int, int, int]]

    @classmethod
    def empty(cls) -> "HelperTrace":
        return cls([], [], [])


class ContractFixture:
    """Deterministic modeled helpers with strict, inspectable call traces."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.trace = HelperTrace.empty()

    @staticmethod
    def get_dis(x1: int, y1: int, x2: int, y2: int) -> int:
        # The reconstructed GetDis contract returns squared Euclidean distance.
        dx, dy = x2 - x1, y2 - y1
        return dx * dx + dy * dy

    @staticmethod
    def get_dir(x1: int, y1: int, x2: int, y2: int) -> int:
        # Historical GetDir is 1-based; coincident points return zero.
        dx, dy = x2 - x1, y2 - y1
        if dx == 0:
            return 0 if dy == 0 else (1 if dy < 0 else 5)
        if dx > 0:
            return 2 if dy < 0 else (3 if dy == 0 else 4)
        return 6 if dy > 0 else (7 if dy == 0 else 8)

    def f_0BE8_0B83(self, x1: int, y1: int, x2: int, y2: int) -> int:
        args = (x1, y1, x2, y2)
        self.trace.distance_calls.append(args)
        return self.get_dis(*args)

    def f_0BE8_0B21(self, x1: int, y1: int, x2: int, y2: int) -> int:
        args = (x1, y1, x2, y2)
        self.trace.direction_calls.append(args)
        return self.get_dir(*args)

    def TileCanBeMovedOn(
        self,
        plane: int,
        nx: int,
        ny: int,
        from_plane: int,
        from_x: int,
        from_y: int,
        digging: int,
    ) -> int:
        args = (plane, nx, ny, from_plane, from_x, from_y, digging)
        self.trace.move_queries.append(args)
        s = self.scenario
        for i, (dx, dy) in enumerate(zip(DX8, DY8)):
            if (nx & 0xFFFF, ny & 0xFFFF) == ((s.x + dx) & 0xFFFF,
                                               (s.y + dy) & 0xFFFF):
                return 1 if (s.movable_mask >> i) & 1 else 0
        raise AssertionError(f"unexpected TileCanBeMovedOn coordinate {args!r}")

    def description(self) -> dict[str, Any]:
        s = self.scenario
        return {
            "kind": "MODELED_CONTRACT_FIXTURE_ONLY",
            "distance": "squared_euclidean_from_reconstructed_GetDis",
            "direction": "1_based_GetDir_from_reconstructed_GetDir; coincident=0",
            "movable_mask": f"0x{s.movable_mask:02x}",
            "TileCanBeMovedOn": {
                "plane": s.plane,
                "from_plane": s.from_plane,
                "from_x": s.from_x,
                "from_y": s.from_y,
                "digging": 1 if s.mode == 2 else 0,
                "unspecified_coordinate": "fail",
            },
            "allowed_accesses": list(ORACLE_HELPERS),
        }


def helper_fixture(scenario: Scenario) -> ContractFixture:
    return ContractFixture(scenario)


def source_contract_model(s: Scenario, fixture: ContractFixture | None = None) -> dict[str, Any]:
    """Model the archived GetMyRandDirs draft for corpus sanity checks only.

    This is not an independent DOS oracle.  It is useful to make sure generated
    cases cover each branch and to give the runner expected callback arguments.
    The common runner must compare original and compiled C directly.
    """
    f = fixture or helper_fixture(s)
    rot, direction = s.rot, s.direction
    threshold = f.f_0BE8_0B83(s.x, s.y, s.a, s.b)
    best = -1
    if threshold > 0:
        best = -2
        ok = [False] * 8
        flag = 1 if s.mode == 2 else 0
        for i, (dx, dy) in enumerate(zip(DX8, DY8)):
            nx, ny = s.x + dx, s.y + dy
            if (nx, ny) != (s.previous_x, s.previous_y):
                if f.TileCanBeMovedOn(s.plane, nx, ny, s.from_plane,
                                      s.from_x, s.from_y, flag):
                    ok[i] = True
                    best = i
        if best >= 0:
            best = -1
            right = left = direction
            if rot == 0:
                for _ in range(8):
                    if ok[right]:
                        best = right
                        direction = f.f_0BE8_0B21(s.x, s.y, s.a, s.b) - 1
                        rot = 1
                        break
                    if ok[left]:
                        best = left
                        direction = f.f_0BE8_0B21(s.x, s.y, s.a, s.b) - 1
                        rot = -1
                        break
                    right = (right + 1) & 7
                    left = (left - 1) & 7
            else:
                found = False
                for _ in range(8):
                    if rot > 0:
                        if ok[right]:
                            found = True
                            break
                    elif ok[left]:
                        right = left
                        found = True
                        break
                    right = (right + 1) & 7
                    left = (left - 1) & 7
                if found:
                    dis = f.f_0BE8_0B83(s.x + DX8[right], s.y + DY8[right], s.a, s.b)
                    if dis <= threshold:
                        direction = f.f_0BE8_0B21(s.x, s.y, s.a, s.b) - 1
                        rot = 0
                    best = right
    return {
        "return": best,
        "rot": rot,
        "direction": direction,
        "writes": {
            "rot": rot != s.rot,
            "direction": direction != s.direction,
        },
        "helper_trace": {
            "distance": f.trace.distance_calls,
            "direction": f.trace.direction_calls,
            "move": f.trace.move_queries,
        },
        "evidence_level": "SOURCE_MODEL_FIXTURE_ONLY",
    }


def _scenario(case_id: str, *, plane: int = 1, x: int, y: int, a: int, b: int,
              rot: int, direction: int, mode: int, from_plane: int,
              from_x: int, from_y: int, previous_x: int,
              previous_y: int, movable_mask: int, seed_group: str) -> Scenario:
    return Scenario(case_id, plane, x, y, a, b, rot, direction, mode,
                    from_plane, from_x, from_y, previous_x, previous_y,
                    movable_mask & 0xff, seed_group)


def directed_scenarios() -> Iterable[Scenario]:
    """Cover every direction, turn bias, rot class and neighbor mask.

    3 rot sign classes x 8 incoming dirs x 256 move masks = 6144 states,
    repeated across coincident, axis, diagonal and longer targets plus both
    representative modes.  Previous-position exclusion is included as a
    second pass for all masks.
    """
    targets = ((0, 0), (4, 0), (-4, 0), (0, 4), (0, -4),
               (3, 3), (3, -3), (-3, 3), (-3, -3), (9, 4))
    rot_values = (0, 1, -1)
    case = 0
    for mode in (0, 2):
        for tx, ty in targets:
            for rot in rot_values:
                for direction in range(8):
                    for mask in range(256):
                        # Centered interior prevents implicit edge behavior
                        # from being mixed with branch-logic coverage.
                        yield _scenario(f"directed-{case:06d}", x=64, y=32,
                                        a=64 + tx, b=32 + ty, rot=rot,
                                        direction=direction, mode=mode,
                                        plane=1 + (case % 3),
                                        from_plane=1 + (mode & 1),
                                        from_x=64, from_y=32,
                                        previous_x=-100, previous_y=-100,
                                        movable_mask=mask, seed_group="directed-mask")
                        case += 1
        # Any previous neighbor can be excluded; each position is tested in
        # all direction/mask states for each rot sign and a subset of headings.
        for prev_i in range(8):
            px, py = 64 + DX8[prev_i], 32 + DY8[prev_i]
            for rot in rot_values:
                for direction in range(8):
                    for mask in range(256):
                        yield _scenario(f"prev-{case:06d}", x=64, y=32,
                                        a=68, b=35, rot=rot,
                                        direction=direction, mode=mode,
                                        plane=1 + (case % 3),
                                        from_plane=1 + (mode & 1),
                                        from_x=64, from_y=32,
                                        previous_x=px, previous_y=py,
                                        movable_mask=mask, seed_group="previous-exclusion")
                        case += 1
    # Out-of-domain and exact grid boundaries exercise signed coordinate
    # arithmetic while helper results remain explicit for every queried tile.
    for n, (x, y) in enumerate(((0, 0), (0, 63), (127, 0), (127, 63),
                                (1, 1), (126, 62))):
        for mask in range(256):
            yield _scenario(f"boundary-{n}-{mask:02x}", x=x, y=y,
                            a=x + (1 if n & 1 else -1),
                            b=y + (1 if n & 2 else -1), rot=(0, 1, -1)[n % 3],
                            direction=n & 7, mode=n % 4, plane=1 + n % 3,
                            from_plane=1 + n % 3,
                            from_x=x, from_y=y,
                            previous_x=x - 1, previous_y=y - 1,
                            movable_mask=mask, seed_group="boundary")


def randomized_scenarios(count: int, seed: int) -> Iterable[Scenario]:
    rng = random.Random(seed)
    modes = (0, 1, 2, 3, 4, 0x7fff)
    rotations = (-2, -1, 0, 1, 2)
    for i in range(count):
        # Primarily valid logical map coordinates, with a smaller signed-edge
        # sample for neighbors that cross the board perimeter.
        if i % 8 == 0:
            x, y = rng.choice((0, 1, 126, 127)), rng.choice((0, 1, 62, 63))
        else:
            x, y = rng.randrange(128), rng.randrange(64)
        if i % 5 == 0:
            a, b = x, y
        elif i % 5 == 1:
            a, b = x + rng.choice((-1, 0, 1)), y + rng.choice((-1, 0, 1))
        else:
            a, b = rng.randrange(128), rng.randrange(64)
        prev_i = rng.randrange(9)
        if prev_i == 8:
            px, py = x + rng.randrange(-2, 3), y + rng.randrange(-2, 3)
        else:
            px, py = x + DX8[prev_i], y + DY8[prev_i]
        yield _scenario(f"random-{seed:08x}-{i:08d}", x=x, y=y,
                        a=a, b=b, rot=rng.choice(rotations),
                        direction=rng.randrange(8), mode=rng.choice(modes),
                        plane=rng.choice((1, 2, 3)),
                        from_plane=rng.choice((1, 2, 3)),
                        from_x=rng.randrange(128), from_y=rng.randrange(64),
                        previous_x=px, previous_y=py,
                        movable_mask=rng.randrange(256), seed_group="random")


def scenario_stream(count: int, seed: int) -> Iterable[Scenario]:
    yield from directed_scenarios()
    yield from randomized_scenarios(count, seed)


def _behavior():
    import behavior
    return behavior


def _word(value: int) -> bytes:
    return (value & 0xFFFF).to_bytes(2, "little")


def _write(name: str, value: int):
    b = _behavior()
    return b.symbol_address(name), _word(value)


def _observe(name: str, size: int = 2):
    b = _behavior()
    return b.Range(name, b.symbol_address(name), size)


def _far_symbol(name: str) -> list[int]:
    record = _behavior().symbol(name)
    if isinstance(record, dict):
        return [int(record["off"]), int(record["seg"])]
    return [int(record.off), int(record.seg)]


def _move_fixture(s: Scenario):
    queried = {}

    def handle(machine, args):
        if len(args) != 7:
            raise AssertionError(f"TileCanBeMovedOn stack shape: {args!r}")
        plane, nx, ny, from_plane, from_x, from_y, digging = (v & 0xFFFF for v in args)
        expected = (s.plane, s.from_plane, s.from_x & 0xFFFF,
                    s.from_y & 0xFFFF, 1 if s.mode == 2 else 0)
        actual = (plane, from_plane, from_x, from_y, digging)
        if actual != expected:
            raise AssertionError(f"unexpected movement-query state {actual!r}; expected {expected!r}")
        for i, (dx, dy) in enumerate(zip(DX8, DY8)):
            if (nx, ny) == ((s.x + dx) & 0xFFFF, (s.y + dy) & 0xFFFF):
                seen = queried.setdefault(id(machine), set())
                if (nx, ny) in seen:
                    raise AssertionError(f"duplicate/unexpected movement query {(nx, ny)!r}")
                seen.add((nx, ny))
                return 1 if (s.movable_mask >> i) & 1 else 0
        raise AssertionError(f"unexpected movement-query coordinate {(nx, ny)!r}")
    return handle


def _tile_fixture_writes(s: Scenario):
    """Materialize the eight-bit contract mask in actual DOS map globals.

    This is used only with an observation-only helper callback, allowing the
    original executable's TileCanBeMovedOn body to run. Coordinates outside
    the applicable map are intentionally left unwritten; the helper rejects
    them before reading a map cell.
    """
    b = _behavior()
    writes = [_write("TERRAINset", 0)]
    map_name = "MapA" if s.plane <= 1 else ("MapB" if s.plane == 2 else "MapR")
    for i, (dx, dy) in enumerate(zip(DX8, DY8)):
        nx, ny = s.x + dx, s.y + dy
        max_x = 127 if map_name == "MapA" else 63
        if not (0 <= nx <= max_x and 0 <= ny <= 63):
            continue
        movable = (s.movable_mask >> i) & 1
        # 0x00 and 0x18 are ordinary walkable values.  0x54 and 0x19 are
        # blocked on the corresponding maps with TERRAINset cleared.
        if map_name == "MapA":
            value = 0x00 if movable else 0x54
        elif not movable:
            value = 0x19
        elif s.mode == 2 and i % 2 == 0:
            # Exercise the diggable tile path as well as ordinary walkable
            # cells. At y==0 the helper also consults the below cell, which
            # the fixture sets to a clear tile below.
            value = 0x20
        else:
            value = 0x18
        address = b.symbol_address(map_name) + nx * 64 + ny
        writes.append((address, bytes((value,))))
    return writes


def direct_tile_cases():
    """Cases for original-versus-C TileCanBeMovedOn contract testing.

    Sweep every map branch around coordinate boundaries, terrain thresholds,
    digging classes and the row-zero/row-one origin rules. Map bytes are the
    only semantic inputs; a LifeA canary is observed to detect accidental
    writes, while this function's source has no LifeA dependency.
    """
    b = _behavior()
    case_no = 0
    coords = ((0, 0), (0, 1), (1, 0), (7, 1), (7, 2),
              (63, 0), (63, 1), (63, 2), (64, 0), (127, 63),
              (-1, 1), (128, 1), (1, -1), (1, 64))
    tiles = (0x00, 0x18, 0x19, 0x1b, 0x1c, 0x1f, 0x20, 0x2e,
             0x2f, 0x30, 0x31, 0x32, 0x53, 0x54, 0x90, 0x91)
    for plane in (0, 1, 2, 3, 4):
        map_name = "MapA" if plane <= 1 else ("MapB" if plane == 2 else "MapR")
        max_x = 127 if map_name == "MapA" else 63
        for x, y in coords:
            if not (0 <= x <= max_x and 0 <= y <= 63):
                # Invalid coordinates still need representative values in
                # registers; no map cell should be touched by the function.
                cell = None
            else:
                cell = b.symbol_address(map_name) + x * 64 + y
            for tile in tiles:
                for terrain in (0, 1):
                    for digging in (0, 1):
                        for origin in (0, 1, 2):
                            from_plane = plane if origin != 2 else (plane + 1)
                            if origin == 0:
                                from_x, from_y = x, y
                            elif origin == 1:
                                from_x, from_y = x + 1, max(0, y - 1)
                            else:
                                from_x, from_y = 0, 0
                            writes = [_write("TERRAINset", terrain)]
                            if cell is not None:
                                writes.append((cell, bytes((tile,))))
                                if y == 0 and map_name != "MapA" and x <= 63:
                                    below = b.symbol_address(map_name) + x * 64 + 1
                                    writes.append((below, b"\x18"))
                            # Stable canary in the analogous LifeA cell when
                            # it is in bounds. The helper must leave it alone.
                            if 0 <= x <= 127 and 0 <= y <= 63:
                                life = b.symbol_address("LifeA") + x * 64 + y
                                writes.append((life, b"\xA7"))
                            yield b.Case(
                                label=f"tile-{case_no:06d}",
                                args=[plane, x, y, from_plane, from_x, from_y, digging],
                                writes=writes,
                                observe=[_observe("TERRAINset"),
                                         b.Range("target_tile", cell, 1) if cell is not None else _observe("TERRAINset"),
                                         b.Range("life_canary", b.symbol_address("LifeA") + x * 64 + y, 1)
                                         if 0 <= x <= 127 and 0 <= y <= 63 else _observe("TERRAINset")],
                                return_kind="s16",
                                metadata={"suite": "tile_can_be_moved_on_contract_v1",
                                          "map": map_name, "tile": tile,
                                          "terrain": terrain, "digging": digging,
                                          "origin_case": origin},
                            )
                            case_no += 1


def randomized_direct_tile_cases(count: int = 5000, seed: int = 0x710ECAFE):
    """Randomized arbitrary-byte map contract cases for TileCanBeMovedOn.

    Unlike the GetMyRandDirs movement-mask corpus, each case supplies an
    independently drawn tile byte (and below-row byte), LifeA state and valid
    HoleMapB/HoleMapR wall coordinates. This checks the helper with its true
    map domain rather than one of two chosen walkability values per neighbor.
    """
    rng = random.Random(seed)
    b = _behavior()
    for i in range(count):
        plane = rng.choice((0, 1, 2, 3, 4))
        map_name = "MapA" if plane <= 1 else ("MapB" if plane == 2 else "MapR")
        max_x = 127 if map_name == "MapA" else 63
        if i % 5 == 0:
            x = rng.choice((0, 1, max_x - 1, max_x))
            y = rng.choice((0, 1, 2, 62, 63))
        else:
            x, y = rng.randrange(max_x + 1), rng.randrange(64)
        from_plane = rng.choice((0, 1, 2, 3, 4))
        from_x = rng.randrange(128 if from_plane <= 1 else 64)
        from_y = rng.randrange(64)
        digging, terrain = rng.randrange(2), rng.randrange(2)
        tile, below = rng.randrange(256), rng.randrange(256)
        cell = b.symbol_address(map_name) + x * 64 + y
        writes = [
            _write("TERRAINset", terrain),
            (cell, bytes((tile,))),
        ]
        if map_name != "MapA" and y == 0:
            writes.append((b.symbol_address(map_name) + x * 64 + 1, bytes((below,))))
        # The unrelated LifeA byte and row/column wall coordinates are chosen
        # independently so accidental dependencies or writes are visible.
        life_positions = set((x * 64 + y,))
        for _ in range(4):
            lx, ly = rng.randrange(128), rng.randrange(64)
            life_positions.add(lx * 64 + ly)
        for pos in sorted(life_positions):
            writes.append((b.symbol_address("LifeA") + pos, bytes((rng.randrange(256),))))
        holes = {}
        for name in ("HoleMapB", "HoleMapR"):
            idx = rng.randrange(64)
            val = rng.randrange(64)
            holes[name] = (idx, val)
            writes.append((b.symbol_address(name) + idx, bytes((val,))))
        observe = [
            _observe("TERRAINset"),
            b.Range("target_tile", cell, 1),
            b.Range("life_target", b.symbol_address("LifeA") + x * 64 + y, 1),
        ]
        for name, (idx, _) in holes.items():
            observe.append(b.Range(name + "_wall", b.symbol_address(name) + idx, 1))
        yield b.Case(
            label=f"tile-random-{seed:08x}-{i:06d}",
            args=[plane, x, y, from_plane, from_x, from_y, digging],
            writes=writes, observe=observe, return_kind="s16",
            metadata={"suite": "tile_can_be_moved_on_arbitrary_map_v1",
                      "seed": seed, "map": map_name, "tile_byte": tile,
                      "below_byte": below if map_name != "MapA" and y == 0 else None,
                      "terrain": terrain, "digging": digging,
                      "holemap_inputs": holes,
                      "lifea_domain": "random bytes at target plus four random valid cells"},
        )


def to_case(s: Scenario, *, actual_tile: bool = False):
    b = _behavior()
    writes = [
        _write("fd_50F6_0EFA", s.rot),
        _write("fd_50F6_0EF8", s.direction),
        _write("fd_50F6_0A8E", s.mode),
        _write("fd_50F6_0AF8", s.from_plane),
        _write("fd_50F6_0AD6", s.from_x),
        _write("fd_50F6_0AE8", s.from_y),
        _write("fd_50F6_0AB6", s.previous_x),
        _write("fd_50F6_0AC6", s.previous_y),
    ]
    if actual_tile:
        writes.extend(_tile_fixture_writes(s))
    # MSC far C uses caller cleanup; the return hook must only pop the far
    # return address, leaving the caller's explicit ADD SP,0x0e intact.
    callback = b.Callback(stack_words=7,
                          handler=None if actual_tile else _move_fixture(s), pop=0)
    return b.Case(
        label=s.case_id,
        args=(_far_symbol("fd_50F6_0EFA") + _far_symbol("fd_50F6_0EF8") +
              [s.plane, s.x, s.y, s.a, s.b]),
        writes=writes,
        observe=[_observe(n) for n in (
            "fd_50F6_0EFA", "fd_50F6_0EF8", "fd_50F6_0A8E",
            "fd_50F6_0AF8", "fd_50F6_0AD6", "fd_50F6_0AE8",
            "fd_50F6_0AB6", "fd_50F6_0AC6")],
        callbacks={"TileCanBeMovedOn": callback},
        return_kind="s16",
        metadata={
            "suite": "get_my_rand_dirs_v1",
            "contract_level": "original_tile_helper_differential" if actual_tile else "helper_fixture_differential",
            "function": DOS_FUNCTION,
            "compared_effects": [
                "s16_return", "rot_pointer_word", "dir_pointer_word",
                "mode/from/previous position globals", "helper call order and args",
                "all final nonstack writes",
            ],
            "helper_provenance": {
                "GetDir/f_0BE8_0B21": "original image function (runner must resolve original code)",
                "GetDis/f_0BE8_0B83": "original image function (runner must resolve original code)",
                "TileCanBeMovedOn": ("original DOS helper; map cells encoded from movable_mask; TERRAINset=0"
                                     if actual_tile else
                                     "explicit bounded movement-mask fixture; not oracle execution"),
            },
            "input": s.as_dict(),
        },
    )


def _case_scenario(case) -> Scenario:
    data = case.metadata["input"]
    return Scenario(
        case_id=data["case_id"], plane=data["plane"], x=data["x"], y=data["y"],
        a=data["a"], b=data["b"], rot=data["rot"],
        direction=data["direction"], mode=data["mode"],
        from_plane=data["from_plane"], from_x=data["from_x"], from_y=data["from_y"],
        previous_x=data["previous_x"], previous_y=data["previous_y"],
        movable_mask=int(data["movable_mask"], 0), seed_group=data["seed_group"],
    )


def iter_cases(*, directed: bool = True, random_seed: int = 0x1686,
               random_count: int = 0, limit_total: int | None = None,
               actual_tile: bool = False):
    scenarios: Iterable[Scenario] = scenario_stream(random_count, random_seed)
    if not directed:
        scenarios = randomized_scenarios(random_count, random_seed)
    if limit_total is not None:
        scenarios = (s for i, s in enumerate(scenarios) if i < limit_total)
    for scenario in scenarios:
        yield to_case(scenario, actual_tile=actual_tile)


def make_cases(function: str = FUNCTION, *, directed: bool = True, random_seed: int = 0x1686,
               random_count: int = 0, limit_total: int | None = None,
               actual_tile: bool = False):
    """Return a streaming case iterator (the directed corpus is intentionally large)."""
    if function not in (FUNCTION, "GetMyRandDirs", DOS_FUNCTION):
        raise KeyError(f"randdirs suite does not handle {function}")
    return iter_cases(directed=directed, random_seed=random_seed,
                      random_count=random_count, limit_total=limit_total,
                      actual_tile=actual_tile)


def run(pair, out, *, function: str = FUNCTION, random_seed: int = 0x1686,
        random_count: int = 0, max_cases: int | None = None,
        actual_tile: bool = False, ledger=None):
    """Run original-vs-candidate comparisons; any mismatch remains a failure."""
    import json
    from pathlib import Path

    if function not in (FUNCTION, "GetMyRandDirs", DOS_FUNCTION):
        raise KeyError(f"randdirs suite does not handle {function}")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cases = iter_cases(random_seed=random_seed, random_count=random_count,
                       limit_total=max_cases, actual_tile=actual_tile)
    processed = directed_processed = randomized_processed = 0
    first_failure = None
    minimized = None
    for case in cases:
        result = pair.compare(case)
        lane = "randomized" if case.label.startswith("random-") else "directed"
        if ledger is not None:
            ledger.record(case, result, lane=lane)
        processed += 1
        if case.label.startswith("random-"):
            randomized_processed += 1
        else:
            directed_processed += 1
        if not result.equal:
            source_scenario = _case_scenario(case)
            minimized_scenario, attempts = minimize_failure(pair, source_scenario)
            minimized = {
                "scenario": minimized_scenario.as_dict(),
                "attempts": attempts,
                "comparison": getattr(pair.compare(to_case(minimized_scenario, actual_tile=actual_tile)), "diff", None),
            }
            first_failure = {
                "case": case.label,
                "difference": getattr(result, "diff", None),
                "oracle_snapshot": result.original,
                "candidate_snapshot": result.candidate,
                "input": source_scenario.as_dict(),
                "minimized": minimized,
                "contract_level": "original_tile_helper_differential" if actual_tile else "helper_fixture_differential",
            }
            # Do not let a known mismatch be hidden by later passing cases.
            break
        if processed % 10_000 == 0:
            (out / "progress.json").write_text(json.dumps({
                "suite": "get_my_rand_dirs_v1", "executed_count": processed,
                "directed_count": directed_processed,
                "randomized_count": randomized_processed,
                "random_seed": random_seed, "status": "RUNNING",
            }, indent=2))
    directed_expected = 222_720 if max_cases is None or max_cases >= 222_720 else max_cases
    randomized_expected = random_count if max_cases is None else max(0, max_cases - 222_720)
    ledger_report = ledger.finalize() if ledger is not None else None
    run_identity = dict(getattr(pair, "identity", None) or {})
    if ledger is not None:
        suite_path = _behavior().ROOT / "tools" / "behavior_suites" / "randdirs.py"
        run_identity.update({
            "suite_id": "get_my_rand_dirs_v1",
            "suite_sha256": __import__("hashlib").sha256(suite_path.read_bytes()).hexdigest(),
        })
    report = {
        "suite": "get_my_rand_dirs_v1",
        "function": DOS_FUNCTION,
        "source_model": "work/takeover/hardtail/seeds/S25_3BA4_5fc31bb8f45f.c",
        "oracle_identity": getattr(pair, "identity", {}).get("oracle_sha256"),
        "directed_count": directed_processed,
        "randomized_count": randomized_processed,
        "random_seed": random_seed,
        "expected_directed_count": directed_expected,
        "expected_randomized_count": randomized_expected,
        "executed_count": processed,
        "mismatches": int(first_failure is not None),
        "first_failure": first_failure,
        "minimized_failure": minimized,
        "status": "UNRESOLVED",
        "fixture_comparison": ("MISMATCH" if first_failure is not None else
                               ("PASS_WITH_ORIGINAL_TILE_HELPER" if actual_tile else "PASS_UNDER_TILE_MASK_FIXTURE")),
        "movement_helper_mode": "original DOS function" if actual_tile else "modeled mask fixture",
        "proof_limit": ("Map cells are synthesized from a movable mask; original helper executes. This does not cover arbitrary map/LifeA state; no BEHAVIOR_EXACT claim"
                        if actual_tile else "TileCanBeMovedOn uses modeled mask fixture; no BEHAVIOR_EXACT claim"),
        "runner_identity": getattr(pair, "identity", None),
        "identity": run_identity,
        "case_ledger": ledger_report,
        "case_ledger_module_sha256": (__import__("hashlib").sha256(
            (_behavior().ROOT / "tools" / "behavior_ledger.py").read_bytes()).hexdigest()
            if ledger is not None else None),
    }
    (out / "randdirs-results.json").write_text(json.dumps(report, indent=2))
    (out / "progress.json").write_text(json.dumps({
        "suite": report["suite"], "executed_count": processed,
        "directed_count": directed_processed, "randomized_count": randomized_processed,
        "random_seed": random_seed,
        "status": "MISMATCH_STOPPED" if first_failure else "COMPLETE_FIXTURE_DIFFERENTIAL",
    }, indent=2))
    return [] if first_failure is None else [first_failure]


def minimize_failure(pair, initial: Scenario) -> tuple[Scenario, int]:
    """Greedily simplify one failing differential case without hiding it."""
    attempts = 0

    def remains_bad(candidate: Scenario) -> bool:
        nonlocal attempts
        attempts += 1
        return not pair.compare(to_case(candidate)).equal

    s = initial
    # The movement mask is the largest discrete search dimension and often
    # admits a compact counterexample after dropping irrelevant neighbors.
    for bit in range(8):
        if (s.movable_mask >> bit) & 1:
            candidate = replace(s, movable_mask=s.movable_mask & ~(1 << bit))
            if remains_bad(candidate):
                s = candidate
    # Preserve the sign semantics while removing arbitrary magnitude.
    simplified_rot = 0 if s.rot == 0 else (1 if s.rot > 0 else -1)
    if simplified_rot != s.rot:
        candidate = replace(s, rot=simplified_rot)
        if remains_bad(candidate):
            s = candidate
    if s.mode != (2 if s.mode == 2 else 0):
        candidate = replace(s, mode=2 if s.mode == 2 else 0)
        if remains_bad(candidate):
            s = candidate
    for field, value in (("plane", 1), ("from_plane", 1),
                         ("from_x", s.x), ("from_y", s.y)):
        if getattr(s, field) != value:
            candidate = replace(s, **{field: value})
            if remains_bad(candidate):
                s = candidate
    # Try a fixed progression toward an interior, one-step target, retaining
    # the failing predicate at each accepted reduction.
    for nx, ny in ((64, 32), (s.x, s.y), (s.x + 1, s.y),
                   (s.x, s.y + 1), (s.x - 1, s.y), (s.x, s.y - 1)):
        candidate = replace(s, x=nx, y=ny)
        if (nx, ny) != (s.x, s.y) and remains_bad(candidate):
            s = candidate
    for tx, ty in ((s.x, s.y), (s.x + 1, s.y), (s.x, s.y + 1),
                   (s.x - 1, s.y), (s.x, s.y - 1)):
        candidate = replace(s, a=tx, b=ty)
        if (tx, ty) != (s.a, s.b) and remains_bad(candidate):
            s = candidate
    for value in (0, 1, -1):
        candidate = replace(s, direction=value & 7)
        if candidate.direction != s.direction and remains_bad(candidate):
            s = candidate
    for i in range(8):
        candidate = replace(s, previous_x=s.x + DX8[i],
                            previous_y=s.y + DY8[i])
        if (candidate.previous_x, candidate.previous_y) != (s.previous_x, s.previous_y) and remains_bad(candidate):
            s = candidate
    return s, attempts


def negative_controls(out):
    """Prove that output-state and unexpected-neighbor mutations are caught.

    Both candidates are scratch whole-module files and pass through the normal
    peer/data gate. The second case deliberately uses the strict modeled
    neighbor boundary so a ninth query must raise instead of being ignored.
    """
    from pathlib import Path
    import behavior
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    base = Path(__file__).resolve().parents[2] / "work/takeover/hardtail/seeds/S25_3BA4_5fc31bb8f45f.c"
    text = base.read_text(encoding="latin1")
    start = text.index("int far o25_3BA4_1686(")
    end = text.find("\nint far ", start + 1)
    if end < 0:
        end = len(text)
    target = text[start:end]
    results = []

    rot_old, rot_new = "*rot = 1;", "*rot = -1;"
    if target.count(rot_old) != 1:
        raise AssertionError("rot mutation anchor is not unique in GetMyRandDirs")
    rot_path = out / "mutant-rot.c"
    rot_path.write_text(text[:start] + target.replace(rot_old, rot_new, 1) + text[end:], encoding="latin1")
    rot_pair = behavior.PreparedPair(FUNCTION, source=rot_path, out=out / "rot-pair")
    s = _scenario("negative-rot", x=64, y=32, a=68, b=35, rot=0,
                  direction=0, mode=0, plane=1, from_plane=1,
                  from_x=64, from_y=32, previous_x=-100, previous_y=-100,
                  movable_mask=0xff, seed_group="negative-control")
    rot_result = rot_pair.compare(to_case(s, actual_tile=True))
    rot_detected = not rot_result.equal
    results.append({"name": "altered_rot_output", "detected": rot_detected,
                    "mutant_source_sha256": behavior.digest(rot_path.read_bytes()),
                    "difference": rot_result.diff,
                    "execution_errors": 0,
                    "actual_tile_helper": True})
    if not rot_detected:
        raise AssertionError("rot output negative control escaped differential")

    loop_old, loop_new = "for (i = 0; i < 8; i++) {", "for (i = 0; i < 9; i++) {"
    if target.count(loop_old) < 1:
        raise AssertionError("neighbor loop mutation anchor missing")
    extra_path = out / "mutant-extra-neighbor.c"
    changed_target = target.replace(loop_old, loop_new, 1)
    extra_path.write_text(text[:start] + changed_target + text[end:], encoding="latin1")
    extra_pair = behavior.PreparedPair(FUNCTION, source=extra_path, out=out / "extra-pair")
    s = _scenario("negative-extra-neighbor", x=64, y=32, a=68, b=35,
                  rot=0, direction=0, mode=0, plane=1, from_plane=1,
                  from_x=64, from_y=32, previous_x=-100, previous_y=-100,
                  movable_mask=0xff, seed_group="negative-control")
    extra_case = to_case(s, actual_tile=True)
    extra_result = extra_pair.compare(extra_case)
    extra_detected = not extra_result.equal
    original_calls = len(extra_result.original["trace"])
    mutant_calls = len(extra_result.candidate["trace"])
    execution_errors = 0
    results.append({"name": "unexpected_ninth_neighbor_query", "detected": extra_detected,
                    "mutant_source_sha256": behavior.digest(extra_path.read_bytes()),
                    "detection": {"kind": "ordered_actual_helper_trace_mismatch",
                                  "original_tile_helper_calls": original_calls,
                                  "mutant_tile_helper_calls": mutant_calls,
                                  "diff": extra_result.diff},
                    "execution_errors": execution_errors,
                    "actual_tile_helper": True})
    if not extra_detected:
        raise AssertionError("unexpected neighbor trace negative control escaped strict fixture")

    report = {"status": "PASS", "controls": results,
              "claim": "diagnostic sensitivity controls only; not proof of function equivalence"}
    (out / "negative-controls.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=100_000,
                        help="random scenarios after the directed corpus")
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0x1686)
    parser.add_argument("--limit-directed", type=int,
                        help="diagnostic cap; never a closure run")
    args = parser.parse_args()
    scenarios = scenario_stream(args.count, args.seed)
    if args.limit_directed is not None:
        scenarios = iter(scenarios)
        for i, scenario in enumerate(scenarios):
            if i >= args.limit_directed:
                break
            print(json.dumps(scenario.as_dict(), sort_keys=True))
        return
    for scenario in scenarios:
        print(json.dumps(scenario.as_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
