from portable.whole_program.conversions.m1b73_queue_source import (
    _has_identifier,
    _replace_identifier,
)


def main() -> int:
    source = (
        '/* fd_5071_03C4 g_9120 */\n'
        'const char *s = "fd_5071_03C4 g_9120";\n'
        "char q = 'g'; // g_9120\n"
        'use(fd_5071_03C4, g_9120);\n'
    )
    converted, slot_count = _replace_identifier(
        source, "fd_5071_03C4", "portable_m1b73_queue_slot(2)")
    converted, status_count = _replace_identifier(
        converted, "g_9120", "portable_m1b73_g9120_low_byte()")
    if slot_count != 1 or status_count != 1:
        return 1
    if "use(portable_m1b73_queue_slot(2), portable_m1b73_g9120_low_byte());" not in converted:
        return 2
    if '"fd_5071_03C4 g_9120"' not in converted or "/* fd_5071_03C4 g_9120 */" not in converted:
        return 3
    if "// g_9120" not in converted or "'g'" not in converted:
        return 4
    if _has_identifier(converted, "fd_5071_03C4") or _has_identifier(converted, "g_9120"):
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
