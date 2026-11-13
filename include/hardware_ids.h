/* Descriptive constants; names and header grouping are ours, not recovered.
 * No original macro names are claimed. Constants never change the compiled code
 * (docs/codegen-rules.md, "Which names count toward declaration numbers").
 */
#ifndef SIMANT_HARDWARE_IDS_H
#define SIMANT_HARDWARE_IDS_H

/* Reset is pulsed at base+6 before probing DSP acknowledgement. Evidence: src/sound/dsp_probe.c:21
 * (snd_probe_dsp_reset_ack). */
#define SND_BLASTER_RESET_OFFSET 0x6

/* Data byte at base+0xa is compared to reset acknowledgement 0xaa. Evidence: src/sound/dsp_probe.c:21
 * (snd_probe_dsp_reset_ack). */
#define SND_BLASTER_READ_OFFSET 0xa

/* Status byte at base+0xe is polled for bit 0x80. Evidence: src/sound/dsp_probe.c:21
 * (snd_probe_dsp_reset_ack). */
#define SND_BLASTER_STATUS_OFFSET 0xe

/* O_APPEND | O_CREAT | O_WRONLY in the pinned MSC runtime. Evidence:
 * C:/tools/msc-6.00ax-archive/INCLUDE/fcntl.h O_APPEND | O_CREAT | O_WRONLY. */
#define DOS_OPEN_APPEND_CREATE_WRONLY 0x109

/* S_IREAD | S_IWRITE in the pinned MSC runtime. Evidence: C:/tools/msc-6.00ax-archive/INCLUDE/sys/stat.h
 * S_IREAD | S_IWRITE. */
#define DOS_CREATE_OWNER_READ_WRITE 0x180

/* Tandy IO base selected for BIOS model byte FC. Evidence: src/sound/device_channels.c:182
 * (snd_init_tandy_channels). */
#define SND_TANDY_AT_IO_BASE 0x1e0

/* Probe adds 0x10 before testing, so 0x210 is first tested. Evidence: src/sound/device_probe.c:135
 * (snd_find_blaster_dsp_base). */
#define SND_BLASTER_PROBE_INITIAL_BASE 0x200

/* Written with one when initializing PS/1 channels. Evidence: src/sound/device_channels.c:230
 * (snd_init_ps1_channels). */
#define PORT_PS1_INITIALIZE 0x203

/* PS/1 PSG frequency and volume output. Evidence: src/sound/psg_voices.c:40 (snd_ps1_set_note). */
#define PORT_PS1_PSG 0x205

/* Driver considers values below this uninitialized and probes again. Evidence:
 * src/sound/device_channels.c:292 (snd_init_blaster_channels). */
#define SND_BLASTER_FIRST_PROBE_BASE 0x210

/* Fallback base when chip detection leaves the IO base zero. Evidence: src/sound/device_channels.c:331
 * (snd_init_regchip_channels). */
#define SND_REGCHIP_DEFAULT_IO_BASE 0x220

/* Loop checks bound before adding 0x10; 0x260 is tested. Evidence: src/sound/device_probe.c:135
 * (snd_find_blaster_dsp_base). */
#define SND_BLASTER_LAST_PROBE_BASE 0x260

/* MPU data byte output and acknowledgement input. Evidence: src/sound/midi_voices.c:205
 * (snd_mpu_write_data). */
#define PORT_MPU_DATA 0x330

/* MPU ready bits read here and commands written here. Evidence: src/sound/midi_voices.c:215
 * (snd_mpu_write_command). */
#define PORT_MPU_STATUS_COMMAND 0x331

/* OPL timer status reads. Evidence: src/sound/device_probe.c:109 (snd_probe_opl_timer). */
#define PORT_OPL_STATUS 0x388

/* Real-mode 0000:0417 keyboard modifier byte; keep long far-pointer encoding. Evidence:
 * src/platform/input_timer.asm:490 (_input_install_hooks); src/ui/map_window.c:672 (MapToYellowAnt). */
#define BIOS_KEYBOARD_FLAGS_FARPTR 0x00000417L

/* O_BINARY | O_RDWR in the pinned MSC runtime. Evidence: C:/tools/msc-6.00ax-archive/INCLUDE/fcntl.h
 * O_BINARY | O_RDWR. */
#define DOS_OPEN_BINARY_RDWR 0x8002

/* O_BINARY | O_CREAT | O_RDWR in the pinned MSC runtime. Evidence:
 * C:/tools/msc-6.00ax-archive/INCLUDE/fcntl.h O_BINARY | O_CREAT | O_RDWR. */
#define DOS_OPEN_BINARY_CREATE_RDWR 0x8102

/* Real-mode F000:FFFE model byte address. Evidence: src/sound/device_channels.c:182
 * (snd_init_tandy_channels). */
#define BIOS_MODEL_BYTE_FARPTR 0xf000fffeL

/* FC00:0000 byte compared with 0x21; no claim about the whole ROM. Evidence: src/sound/device_probe.c:60
 * (snd_probe_tandy_sound). */
#define SND_TANDY_ROM_PROBE_FARPTR 0xfc000000L

#endif
