# Generated native video startup v1

Finite native-only execution of actual central generated `root_m205F.c` / `root_m1B28.c` for selected EGA profile 0 and VGA profile 8. The S20 `o20_39C7_0211` and `_0005` bodies are exact empty bodies extracted from the pinned generated S20 TU and archived in `derived-source-empty-entries.c`.

Reproduce from repository root with `python portable/tests/whole_program/platform/run_native_video_startup_test.py --report build/workers/native_video_startup_replay.json` (choose a fresh output path). It is not DOS equivalence: the S21 BIOS descriptor and database object services are controlled host boundaries; unsupported hardware branches fail closed. The report records source hashes before/after, compiler executable, compiler subtools, flags, and temporary executable hash. The original DOS binary is not included.
