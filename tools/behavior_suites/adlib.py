"""Oracle-backed contract suite for the AdLib volume/pitch helper.

Runs f_2815_0165 against the original executable and its current whole-module
C draft. The register-helper callback observes call boundaries then falls through
to original assembly; status-port reads use a deterministic provider because the
historical delay routine's fixed IN/LOOP values do not affect returned state.
No proof status is assigned here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import struct
import sys
import time
from dataclasses import replace
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/functions.json').is_file())

import behavior
import behavior_ledger

TARGET = "f_2815_0165"
SUITE = "adlib_register_contract_v1"
INSTRUMENT_TABLE = "fd_50F6_0000"
VOLUME_OFFSET = "fd_50F6_4B16"
OUT_LEVEL_TABLE = "fd_55B3_6BA4"
DATA_SEG = 0xA000
DATA_OFF = 0x2000
INSTR_COUNT = 56
INSTR_STRIDE = 6
INSTR_BYTES = 16


def _word(value: int) -> bytes:
    return struct.pack("<H", value & 0xFFFF)


def _far(offset: int, segment: int) -> bytes:
    return struct.pack("<HH", offset & 0xFFFF, segment & 0xFFFF)


def _signed16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def _range(symbol: str, size: int, name: str | None = None):
    return behavior.Range(name or symbol, behavior.symbol_address(symbol), size)


def instrument_bytes(instr: int, level: int, key_transpose: int, volume_adjust: int) -> bytes:
    raw = bytearray(((instr * 29 + i * 43 + 0x37) & 0xFF) for i in range(INSTR_BYTES))
    raw[2] = level & 0xFF
    struct.pack_into("<h", raw, 11, _signed16(key_transpose))
    struct.pack_into("<h", raw, 13, _signed16(volume_adjust))
    return bytes(raw)


def adlib_case(label: str, *, instr=0, note=60, vol=64, voice=0,
               global_volume_offset=-40, level=0x35, key_transpose=0,
               instrument_volume_adjust=0, status_byte=0):
    """Create a valid 56-record instrument table with the selected entry populated."""
    table = behavior.symbol_address(INSTRUMENT_TABLE) + (instr & 0xFFFF) * INSTR_STRIDE
    volume_global = behavior.symbol_address(VOLUME_OFFSET)
    data_address = DATA_SEG * 16 + DATA_OFF
    pdata = instrument_bytes(instr, level, key_transpose, instrument_volume_adjust)
    writes = [
        (table, _word(instr) + _far(DATA_OFF, DATA_SEG)),
        (data_address, pdata),
        (volume_global, _word(global_volume_offset)),
    ]
    return behavior.Case(
        label=label,
        args=[instr & 0xFFFF, note & 0xFFFF, vol & 0xFFFF, voice & 0xFFFF],
        writes=writes,
        observe=[
            behavior.Range("instrument_record", table, INSTR_STRIDE),
            behavior.Range("instrument_data", data_address, INSTR_BYTES),
            behavior.Range("driver_volume_offset", volume_global, 2),
        ],
        callbacks={"f_283E_000A": behavior.Callback(stack_words=2)},
        return_kind="void",
        io_reads={0x388: status_byte},
        metadata={
            "suite": SUITE,
            "contract": "ordered OPL index/data OUT pairs, helper call arguments, original/candidate non-stack writes and caller ABI",
            "helper_policy": "f_283E_000A is observed with no handler, then original genuine assembly executes; port 0388h IN supplies a fixed status byte",
            "io_delay_evidence": "src/root/m283E.asm f_283E_0020 writes index to DX=0388h, executes exactly ten IN/LOOP reads at 0388h, increments DX and writes data to 0389h, decrements DX and executes exactly forty more IN/LOOP reads at 0388h; IN results are overwritten or AX is restored before output and never control branches",
            "valid_fixture": {"instrument_index": "0..55 record in the 56-entry six-byte table", "voice": "0..8 OPL channel maps", "note": "7-bit note domain plus explicit transposition and endpoint probes", "volume": "all 0..255 byte values; signed/wide edge cases separately tagged"},
        },
        callee_pop=0,
    )


def directed_cases():
    cases = []
    # All byte velocity values over all nine OPL voices, with valid note values
    # and rotating instrument/parameter fixtures.
    for voice in range(9):
        for vol in range(256):
            cases.append(adlib_case(
                f"voice-volume/v{voice}/vol{vol}", instr=(voice * 7 + vol) % INSTR_COUNT,
                note=(17 * voice + 5 * vol) % 128, vol=vol, voice=voice,
                global_volume_offset=-40,
                level=(vol * 37 + voice * 11) & 0xFF,
                key_transpose=((vol + voice) % 5 - 2),
                instrument_volume_adjust=(vol % 17) - 8))
    # Touch every instrument index across all channels, with boundary note and
    # parameter values. This distinguishes pointer selection and register maps.
    for instr in range(INSTR_COUNT):
        for voice in range(9):
            note = (instr * 13 + voice * 7) % 128
            cases.append(adlib_case(
                f"instrument-channel/i{instr}/v{voice}", instr=instr, note=note,
                vol=(instr * 19 + voice * 23) & 0xFF, voice=voice,
                global_volume_offset=-40, level=(instr * 31 + voice * 17) & 0xFF,
                key_transpose=(instr % 7) - 3,
                instrument_volume_adjust=(voice % 9) - 4))
    # Cross high-information signed/clamp cases through every voice.
    for voice in range(9):
        for goff in (-32768, -128, -41, -40, -1, 0, 1, 127, 128, 32767):
            for vol in (0, 1, 63, 127, 128, 255, 0x7FFF, 0x8000, 0xFFFF):
                cases.append(adlib_case(
                    f"signed-clamp/v{voice}/g{goff}/vol{vol:04x}", instr=(voice * 5 + 17) % INSTR_COUNT,
                    note=60, vol=vol, voice=voice, global_volume_offset=goff,
                    level=0xFF, key_transpose=0, instrument_volume_adjust=0))
    # Exercise all 7-bit notes, range edges after octave adjustment, including
    # cases where the source must suppress frequency/key-on register writes.
    for voice in range(9):
        for note in list(range(128)) + [-13, -12, -1, 128, 139, 140, 32767, 0x8000, 0xFFFF]:
            cases.append(adlib_case(
                f"note-edge/v{voice}/n{note:04x}", instr=(voice * 3 + 1) % INSTR_COUNT,
                note=note, vol=73, voice=voice, global_volume_offset=-40,
                level=0xC7, key_transpose=(note % 5) - 2,
                instrument_volume_adjust=-3))
    return cases


def random_cases(count=3000, seed=0x28150165):
    rng = random.Random(seed)
    cases = []
    for i in range(count):
        cases.append(adlib_case(
            f"random/{seed:08x}/{i}", instr=rng.randrange(INSTR_COUNT),
            note=rng.randrange(128), vol=rng.randrange(256), voice=rng.randrange(9),
            global_volume_offset=rng.choice((-40, -1, 0, 1, rng.randrange(-128, 129))),
            level=rng.randrange(256), key_transpose=rng.randrange(-3, 4),
            instrument_volume_adjust=rng.randrange(-16, 17),
            status_byte=rng.choice((0x00, 0xFF, 0x55, 0xAA))))
    return cases










