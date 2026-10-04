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










