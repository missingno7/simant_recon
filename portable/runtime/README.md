The BIOS font files are native hardware resources used by the BIOS font adapter.
They are captured from the pinned DOSBox-X v2026.08.31 BIOS ROM while the
canonical DOS build is running with the configured Czech keyboard layout. The
adjacent bios-reference/manifest.json records the source files, runtime capture,
byte lengths, SHA256 identities and GPL-2.0-or-later license. They are emulator
service data, not recovered SimAnt game state. The native builder copies these
explicit platform resources to its output, and copies only the eleven resource
files listed in platform.json from the historical assets directory. Historical
executables are not runtime inputs.

INSTALL.EXE in the build runtime directory is an explicitly generated empty
filesystem probe, SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.
Canonical src/root/m15F8.c main opens that filename five times and then closes
all five handles. It never reads or executes its contents. The host file opens
and closes are real; the original installer is not copied, pinned or executed.
