# Converted source window loader

Run `python portable/tests/whole_program/window_source_loader/test_preword_adapter.py`
to check the source-side adapter and negative controls. The current converted
loader receipt was produced with
`python portable/tests/whole_program/window_source_loader/run_v2.py`; that
runner is write-once and refuses to overwrite
`evidence/window-loader-hcegant-v2.json`.

The earlier `run.py`/v1 report exercised the pre-central-conversion generated
TU snapshot. It is retained for provenance, but the current generated loader
already has the adapter applied and should be tested with the v2 runner.

The original loader body remains responsible for resource lookup order,
count-field copies, the profile rectangle memcpy, purge-list iteration, color
copy length, and purge calls. Only the downstream `win_LoadWindow` call is
replaced in this focused test with an ID recorder. Font initialization, lock
initialization, bitmap-size query, and object unhook are order-recording host
services. This validates converted-source/resource integration; it is not a
DOS differential or a claim that all downstream window loading is integrated.

The global owner is in `portable/whole_program/window_source_globals.{h,c}`.
The source Rect table has a shared fixed-width declaration in
`window_source_rects.h`. The row pointer for `win_colors` is allocated only
after resource 0x80 sets `win_numOfColors` and before the source loads resource
0x81. Consumers of the original incomplete array declaration must pass through
`convert_window_global_declarations` so they load through the native pointer.
