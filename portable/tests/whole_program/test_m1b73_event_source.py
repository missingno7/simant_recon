from pathlib import Path

from portable.whole_program.conversions.m1b73_event_source import adapt


ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    cases = (
        ("src/S19/m384C.c", 1, 1),
        ("src/S10/m35F5.c", 2, 1),
    )
    for path, four, five in cases:
        source = (ROOT / path).read_text(encoding="utf-8")
        output, ledger = adapt(source, path)
        if ledger["four_word_calls"] != four or ledger["five_word_calls"] != five:
            return 1
        if output.count("portable_m1b73_event_enqueue_four_word_command(") != four:
            return 2
        if output.count("f_1B73_030F(") != five:
            return 3
        if "extern void far f_1B73_030F();" in output:
            return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
