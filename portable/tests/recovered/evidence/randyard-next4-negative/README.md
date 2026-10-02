# RandYard next4 differential negative control

These immutable diagnostic runs use the next4 generated source profile and
the frozen DOS executable. They do not claim behavioral closure.

Scenarios 1 and 3 complete in the DOS emulator. In both, final S-RNG and C-RNG
states agree, as do the rest of the imported fields, but the first ant-lion
position differs and 18 nearby `MapA` bytes differ. The reports pin the native
snapshot, each compiled input, and the frozen executable identity. This is the
expected negative control for the source expression evaluation-order fix
planned in the next versioned profile.

Scenario 2 was attempted but the DOS VM stopped at `INT 21h` because that path's
environmental service is not modeled by this harness. It is not a test result.

The repeat report is retained only as diagnostic history. Its DOS lane rebuilt
a fresh VM from the exported `pre-repeat` semantic fields rather than replaying
the first action in the same VM, so unprojected translation-unit state was not
preserved. Do not use its repeat comparison as evidence.
