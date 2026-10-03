"""Final preword alias conversion for root m1FD2's shared menu state."""

from __future__ import annotations

import hashlib
import re


SOURCE_PATH = "src/root/m1FD2.c"
SOURCE_SHA256 = "f4359bdaf4cfc0fe326a54cf8a1eacb9ba3098b710bf2a561b3d0f48569bf6d8"
HEADER = '#include "portable/whole_program/menu_globals.h"\n'


def _text(value: str | bytes) -> str:
    return value.decode("utf-8") if isinstance(value, bytes) else value


def adapt_transformed(source: str | bytes, rel: str,
                      original_source: str | bytes) -> tuple[str, dict]:
    """Make root menu consumers use the S17-loaded canonical sidecar owner.

    Call after `source_runtime_globals.adapt_transformed` and before word
    lowering. `original_source` is the immutable raw m1FD2 source for pinning;
    `source` may include earlier reviewed preword overlays.
    """
    original = original_source.encode("utf-8") if isinstance(original_source, str) else original_source
    if rel != SOURCE_PATH:
        raise ValueError(f"unregistered shared menu owner source: {rel}")
    if hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise ValueError("canonical root m1FD2 source identity drift")

    text = _text(source)
    declaration = re.compile(
        r"(?m)^\s*struct\s+MenuData\s+far\s+\*\s*g_6054\s*=\s*0\s*;\s*$")
    text, declaration_count = declaration.subn("", text, count=1)
    if declaration_count != 1:
        raise ValueError("expected exactly one root g_6054 storage declaration")

    title_pattern = re.compile(r"\bg_6054\s*->\s*titles\b")
    item_pattern = re.compile(r"\bg_6054\s*->\s*items\b")
    loaded_pattern = re.compile(r"!\s*g_6054\b")
    text, title_count = title_pattern.subn("g_menu_view.titles", text)
    text, item_count = item_pattern.subn("g_menu_view.items", text)
    text, loaded_count = loaded_pattern.subn("fd_55B3_6054 == NULL", text)
    # The preceding runtime adapter adds one source-count traversal to size
    # native title geometry; its seven historical reads therefore become eight.
    if "sim_source_runtime_reserve_menu_titles" not in text:
        raise ValueError("native menu geometry reserve adaptation must precede alias conversion")
    if (title_count, item_count, loaded_count) != (8, 6, 2):
        raise ValueError(
            "root menu consumer inventory drift: "
            f"titles={title_count} items={item_count} loaded-checks={loaded_count}")
    if re.search(r"\bg_6054\b", text):
        raise ValueError("root menu private g_6054 storage/reference remains")

    if HEADER.strip() not in text:
        text = HEADER + text
    return text, {
        "kind": "ROOT_MENU_USES_S17_SHARED_OWNER",
        "source": SOURCE_PATH,
        "canonical_source_sha256": SOURCE_SHA256,
        "input_sha256": hashlib.sha256(_text(source).encode("utf-8")).hexdigest(),
        "output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "removed_private_storage": declaration_count,
        "title_views_to_g_menu_view": title_count,
        "item_views_to_g_menu_view": item_count,
        "loaded_checks_to_fd_55b3_6054": loaded_count,
        "capacity_basis": "The typed sidecar owns one titles vector and 16 item-vector pointers. The real SHARED id 0 resource has five titles and six populated table pointers; root accesses separate typed fields, never casts that short table vector to MenuData.",
    }

