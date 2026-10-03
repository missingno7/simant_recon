#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/audio_state.h"
#pragma pack(push, 2)
/* Data-only translation unit (hypothesis): sound effect instrument tables, DGROUP _DATA
   00B8-1811 (the object right before module 0000's _DATA at 1812).
   Evidence: the nine instrument tables (0C42 + 9 x 336) point into this object's own data through
   _DATA segment fixups (S27 relocations #570-#1048, one ascending run of LEDATA records, descending
   inside each record), so the MIDI maps, FM patches and samples at 00B8-0A81 are defined here; no
   code module references any of it through its own segment (277E, 295C, 0000, 2815 and 290D use
   external symbols and have their _DATA elsewhere), and no module with code links before 0000.
   Layout of struct Sample (packed, 31 bytes) as in modules 0000/290D; each sample is a separate
   variable (word-aligned, one pad byte).  FM patch fields as read by 2815 (+0Bh octave shift,
   +0Dh volume); MIDI map int[3] as read by 295C (key/program, volume offset, transpose).
   Instrument kinds dispatch through 295C's device tables: 1 DAC (290D), 2 FM (2815),
   3/4/5 PSG devices (29D6), 6 MIDI melodic, 7 MIDI percussion (295C). */

typedef char  *  *Handle;

#pragma pack(1)


struct FMPatch {
    uint8_t reg[11];
    int16_t octave;
    int16_t volume;
};
#pragma pack(2)



struct SfxNote {
    int16_t note;
    int16_t kind;
    int16_t sound;
    int16_t volume;
};

enum { SND_NONE, SND_DAC, SND_FM, SND_PSG3, SND_PSG4, SND_PSG5, SND_MIDI, SND_MIDIDRUM };

static int16_t midiMap[55][3] = {
    { 103, -30, -14 }, { 122, 0, 0 }, { 122, 0, 0 }, { 71, 0, 0 }, { 122, 0, 0 }, { 122, 0, 0 },
    { 122, 0, 0 }, { 124, 0, 0 }, { 26, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 },
    { 69, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { 37, 0, 0 }, { -1, 0, 0 }, { 62, 0, 0 },
    { 63, 0, 0 }, { 64, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 },
    { -1, 0, 0 }, { 70, -10, 0 }, { 108, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 },
    { -1, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { 81, 0, 0 }, { 35, 0, 0 },
    { 94, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { 104, 0, 0 },
    { -1, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { -1, 0, 0 }, { 114, 0, -12 }, { -1, 0, 0 },
    { 63, 0, 0 }, { -1, 0, 0 }, { 113, 0, -24 }, { 64, 0, 0 }, { 101, 0, 0 }, { 19, 0, 0 },
    { 39, 0, 0 }
};

static struct FMPatch fm00 = { { 0x01, 0x07, 0x80, 0x87, 0xF0, 0xF0, 0x05, 0x05, 0x02, 0x03, 0x00 }, 0, 0 };
static struct FMPatch fm01 = { { 0x00, 0x86, 0x00, 0x80, 0xF9, 0xFF, 0xFF, 0x0F, 0x02, 0x00, 0x00 }, 0, 0 };
static struct FMPatch fm02 = { { 0x11, 0x32, 0x00, 0x44, 0xF5, 0xF8, 0x7F, 0xFF, 0x0C, 0x00, 0x00 }, 0, 0 };
static struct FMPatch fm03 = { { 0xC4, 0x06, 0x00, 0x00, 0xFB, 0xFF, 0xFF, 0xF0, 0x0C, 0x00, 0x00 }, 0, 0 };
static struct FMPatch fm04 = { { 0x00, 0x00, 0x00, 0x0B, 0xF6, 0xFA, 0x8F, 0x6F, 0xFE, 0x00, 0x00 }, 0, 0 };
static struct FMPatch fm05 = { { 0x10, 0x32, 0x00, 0x42, 0xF5, 0xF8, 0x7F, 0xFF, 0x0C, 0x00, 0x00 }, 0, 0 };
static struct FMPatch fm06 = { { 0x11, 0x00, 0x80, 0x02, 0xF0, 0xF0, 0xFF, 0xFF, 0x04, 0x00, 0x00 }, 0, 0 };
static struct FMPatch fm07 = { { 0xC0, 0x60, 0x00, 0x07, 0xF4, 0xF0, 0x44, 0x00, 0x04, 0x00, 0x00 }, -2, -25 };
static struct FMPatch fm08 = { { 0x81, 0xF0, 0x00, 0x05, 0xF4, 0x98, 0x4A, 0x16, 0x00, 0x00, 0x00 }, -1, -20 };
static struct FMPatch fm09 = { { 0xC0, 0xE4, 0x00, 0x0E, 0xF3, 0xFF, 0x07, 0x3F, 0xFE, 0x00, 0x01 }, -3, -40 };
static struct FMPatch fm10 = { { 0x12, 0x00, 0x80, 0x8F, 0x92, 0xF2, 0xF2, 0x60, 0x08, 0x00, 0x00 }, -1, 15 };
static struct FMPatch fm11 = { { 0x17, 0x10, 0x00, 0x00, 0xFF, 0xF0, 0x07, 0xF0, 0x0C, 0x00, 0x00 }, -3, -5 };
static struct FMPatch fm12 = { { 0x11, 0x33, 0x00, 0xC0, 0xF8, 0xF8, 0xFF, 0xFF, 0x0A, 0x00, 0x00 }, -1, 0 };
static struct FMPatch fm13 = { { 0x00, 0x00, 0x00, 0x0B, 0xF6, 0xFA, 0x8F, 0x6F, 0xFE, 0x00, 0x00 }, -2, 0 };
static struct FMPatch fm14 = { { 0x00, 0x00, 0x00, 0x0B, 0xD6, 0xA8, 0x4F, 0x6C, 0xFE, 0x00, 0x00 }, -2, -30 };
static struct FMPatch fm15 = { { 0x10, 0x30, 0x00, 0x46, 0xF5, 0xF8, 0x7F, 0xFF, 0x06, 0x00, 0x00 }, -2, 0 };
static struct FMPatch fm16 = { { 0x0E, 0x0E, 0x00, 0x00, 0x88, 0xF0, 0x75, 0x00, 0x0C, 0x00, 0x00 }, 0, 0 };
static struct FMPatch fm17 = { { 0x08, 0x8C, 0x00, 0x47, 0x98, 0xEF, 0x45, 0x03, 0x0C, 0x00, 0x00 }, 0, 0 };
static struct FMPatch fm18 = { { 0xE5, 0xF0, 0x00, 0x00, 0x65, 0xFF, 0x0B, 0xA0, 0xFE, 0x00, 0x00 }, 0, 0 };
static struct FMPatch fm19 = { { 0x0E, 0x0E, 0x00, 0x00, 0x74, 0xF0, 0xF7, 0xF0, 0x0C, 0x00, 0x00 }, 0, 0 };

static PortableWholeAudioSample s_sinwave = { 0, 0, 0, 0, 2, 0, 0, "sinwave.adp", 55 };
static PortableWholeAudioSample s_square3 = { 0, 0, 0, 0, 3, 0, 0, "square.adp", 56 };
static PortableWholeAudioSample s_square4 = { 0, 0, 0, 0, 4, 0, 0, "square.adp", 56 };
static PortableWholeAudioSample s_agogo = { 0, 0, 0, 0, 5, -14, 0, "agogo.adp", 0 };
static PortableWholeAudioSample s_alert1 = { 0, 0, 0, 0, 5, 0, 0, "alert1.adp", 1 };
static PortableWholeAudioSample s_alert2 = { 0, 0, 0, 0, 5, 0, 0, "alert2.adp", 2 };
static PortableWholeAudioSample s_bassass = { 0, 0, 0, 0, 4, 6, 0, "bassass.adp", 3 };
static PortableWholeAudioSample s_beep1 = { 0, 0, 0, 0, 5, 0, 0, "beep1.adp", 4 };
static PortableWholeAudioSample s_beep2 = { 0, 0, 0, 0, 5, 0, 0, "beep2.adp", 5 };
static PortableWholeAudioSample s_beep3 = { 0, 0, 0, 0, 5, 0, 0, "beep3.adp", 6 };
static PortableWholeAudioSample s_birdcall = { 0, 0, 0, 0, 5, 0, 0, "birdcall.adp", 7 };
static PortableWholeAudioSample s_brasssyn = { 0, 0, 0, 0, 5, 0, 0, "brasssyn.adp", 8 };
static PortableWholeAudioSample s_bugspray = { 0, 0, 0, 0, 5, 0, 0, "bugspray.adp", 9 };
static PortableWholeAudioSample s_burp = { 0, 0, 0, 0, 5, 0, 0, "burp.adp", 10 };
static PortableWholeAudioSample s_buzzing = { 0, 0, 0, 0, 5, 0, 0, "buzzing.adp", 11 };
static PortableWholeAudioSample s_cabasa = { 0, 0, 0, 0, 5, -4, 0, "cabasa.adp", 12 };
static PortableWholeAudioSample s_catmeow = { 0, 0, 0, 0, 5, 0, 0, "catmeow.adp", 13 };
static PortableWholeAudioSample s_catyowl = { 0, 0, 0, 0, 5, 0, 0, "catyowl.adp", 14 };
static PortableWholeAudioSample s_click = { 0, 0, 0, 0, 5, 0, 0, "click.adp", 15 };
static PortableWholeAudioSample s_click2 = { 0, 0, 0, 0, 5, 0, 0, "click2.adp", 16 };
static PortableWholeAudioSample s_dig1 = { 0, 0, 0, 0, 5, 0, 0, "dig1.adp", 17 };
static PortableWholeAudioSample s_dig2 = { 0, 0, 0, 0, 5, 0, 0, "dig2.adp", 18 };
static PortableWholeAudioSample s_dig3 = { 0, 0, 0, 0, 5, 0, 0, "dig3.adp", 19 };
static PortableWholeAudioSample s_dogfoot = { 0, 0, 0, 0, 5, 0, 0, "dogfoot.adp", 20 };
static PortableWholeAudioSample s_dogwhim1 = { 0, 0, 0, 0, 5, 0, 0, "dogwhim1.adp", 21 };
static PortableWholeAudioSample s_dogwhim2 = { 0, 0, 0, 0, 5, 0, 0, "dogwhim2.adp", 22 };
static PortableWholeAudioSample s_dogyap = { 0, 0, 0, 0, 5, 0, 0, "dogyap.adp", 23 };
static PortableWholeAudioSample s_doorslam = { 0, 0, 0, 0, 5, 0, 0, "doorslam.adp", 24 };
static PortableWholeAudioSample s_dreamgui = { 0, 0, 0, 0, 4, -4, 0, "dreamgui.adp", 25 };
static PortableWholeAudioSample s_drip1 = { 0, 0, 0, 0, 5, 0, 0, "drip1.adp", 26 };
static PortableWholeAudioSample s_drip2 = { 0, 0, 0, 0, 5, 0, 0, "drip2.adp", 27 };
static PortableWholeAudioSample s_dropegg = { 0, 0, 0, 0, 5, 0, 0, "dropegg.adp", 28 };
static PortableWholeAudioSample s_dropfood = { 0, 0, 0, 0, 5, 0, 0, "dropfood.adp", 29 };
static PortableWholeAudioSample s_droprock = { 0, 0, 0, 0, 5, 0, 0, "droprock.adp", 30 };
static PortableWholeAudioSample s_fooddrip = { 0, 0, 0, 0, 5, 0, 0, "fooddrip.adp", 31 };
static PortableWholeAudioSample s_foodslop = { 0, 0, 0, 0, 5, 0, 0, "foodslop.adp", 32 };
static PortableWholeAudioSample s_foodunsl = { 0, 0, 0, 0, 5, 0, 0, "foodunsl.adp", 33 };
static PortableWholeAudioSample s_humanfoo = { 0, 0, 0, 0, 5, 0, 0, "humanfoo.adp", 34 };
static PortableWholeAudioSample s_kick = { 0, 0, 0, 0, 5, -4, 0, "kick.adp", 35 };
static PortableWholeAudioSample s_lawnmowr = { 0, 0, 0, 0, 5, 0, 0, "lawnmowr.adp", 36 };
static PortableWholeAudioSample s_lioncrun = { 0, 0, 0, 0, 5, 0, 0, "lioncrun.adp", 37 };
static PortableWholeAudioSample s_lionroar = { 0, 0, 0, 0, 5, 0, 0, "lionroar.adp", 38 };
static PortableWholeAudioSample s_lionsnar = { 0, 0, 0, 0, 5, 0, 0, "lionsnar.adp", 39 };
static PortableWholeAudioSample s_pop = { 0, 0, 0, 0, 5, 0, 0, "pop.adp", 40 };
static PortableWholeAudioSample s_rain = { 0, 0, 0, 0, 5, 0, 0, "rain.adp", 41 };
static PortableWholeAudioSample s_retch = { 0, 0, 0, 0, 5, 0, 0, "retch.adp", 42 };
static PortableWholeAudioSample s_shaker = { 0, 0, 0, 0, 5, -4, 0, "shaker.adp", 43 };
static PortableWholeAudioSample s_slurp = { 0, 0, 0, 0, 5, 0, 0, "slurp.adp", 44 };
static PortableWholeAudioSample s_slurplng = { 0, 0, 0, 0, 5, 0, 0, "slurplng.adp", 45 };
static PortableWholeAudioSample s_snare = { 0, 0, 0, 0, 4, -4, 0, "snare.adp", 46 };
static PortableWholeAudioSample s_spiderft = { 0, 0, 0, 0, 5, 0, 0, "spiderft.adp", 47 };
static PortableWholeAudioSample s_stick = { 0, 0, 0, 0, 5, -4, 0, "stick.adp", 48 };
static PortableWholeAudioSample s_tearing = { 0, 0, 0, 0, 5, 0, 0, "tearing.adp", 49 };
static PortableWholeAudioSample s_tom = { 0, 0, 0, 0, 5, -4, 0, "tom.adp", 50 };
static PortableWholeAudioSample s_whap = { 0, 0, 0, 0, 5, -4, 0, "whap.adp", 51 };
static PortableWholeAudioSample s_whistle = { 0, 0, 0, 0, 5, -4, 0, "whistle.adp", 52 };
static PortableWholeAudioSample s_keys = { 0, 0, 0, 0, 5, 0, 0, "keys.adp", 53 };
static PortableWholeAudioSample s_ooohs = { 0, 0, 0, 0, 5, -19, 0, "ooohs.adp", 54 };

struct SfxNote fd_55B3_0A82[56] = {
    { 60, 3, 0, 127 }, { 60, 3, 1, 127 }, { 60, 3, 2, 127 }, { 60, 3, 3, 127 }, { 60, 3, 4, 127 }, { 60, 3, 5, 127 },
    { 60, 3, 6, 127 }, { 60, 3, 7, 127 }, { 60, 3, 8, 127 }, { 60, 3, 9, 127 }, { 60, 3, 10, 127 }, { 60, 3, 11, 127 },
    { 60, 3, 12, 127 }, { 60, 3, 13, 127 }, { 60, 3, 14, 127 }, { 60, 3, 15, 127 }, { 60, 3, 16, 127 }, { 60, 2, 17, 127 },
    { 60, 2, 18, 127 }, { 60, 2, 19, 127 }, { 60, 3, 20, 127 }, { 60, 3, 21, 127 }, { 60, 3, 22, 127 }, { 60, 3, 23, 127 },
    { 60, 3, 24, 127 }, { 60, 3, 25, 127 }, { 60, 3, 26, 127 }, { 60, 3, 27, 127 }, { 60, 3, 28, 127 }, { 60, 3, 29, 127 },
    { 60, 3, 30, 127 }, { 60, 3, 31, 127 }, { 60, 3, 32, 127 }, { 60, 3, 33, 127 }, { 60, 3, 34, 127 }, { 60, 3, 35, 127 },
    { 60, 3, 36, 127 }, { 60, 3, 37, 127 }, { 60, 3, 38, 127 }, { 60, 3, 39, 127 }, { 60, 3, 40, 127 }, { 60, 3, 41, 127 },
    { 60, 3, 42, 127 }, { 60, 3, 43, 127 }, { 60, 3, 44, 127 }, { 60, 3, 45, 127 }, { 60, 3, 46, 127 }, { 60, 3, 47, 127 },
    { 60, 3, 48, 127 }, { 60, 3, 49, 127 }, { 60, 3, 50, 127 }, { 60, 3, 51, 127 }, { 60, 3, 52, 127 }, { 60, 3, 53, 127 },
    { 60, 3, 54, 127 }, { 100, 4, 10, 127 }
};

PortableWholeAudioInstrumentEntry fd_55B3_0C42[56] = {
    { SND_DAC, &s_kick }, { SND_DAC, &s_alert1 }, { SND_DAC, &s_alert2 }, { SND_DAC, &s_square3 },
    { SND_DAC, &s_beep1 }, { SND_DAC, &s_beep2 }, { SND_DAC, &s_beep3 }, { SND_DAC, &s_birdcall },
    { SND_DAC, &s_brasssyn }, { SND_DAC, &s_bugspray }, { SND_DAC, &s_burp }, { SND_DAC, &s_buzzing },
    { SND_DAC, &s_cabasa }, { SND_DAC, &s_catmeow }, { SND_DAC, &s_catyowl }, { SND_DAC, &s_kick },
    { SND_DAC, &s_kick }, { SND_DAC, &s_kick }, { SND_DAC, &s_dig2 }, { SND_DAC, &s_dig3 },
    { SND_DAC, &s_dogfoot }, { SND_DAC, &s_dogwhim1 }, { SND_DAC, &s_dogwhim2 }, { SND_DAC, &s_dogyap },
    { SND_DAC, &s_doorslam }, { SND_DAC, &s_square3 }, { SND_DAC, &s_drip1 }, { SND_DAC, &s_drip2 },
    { SND_DAC, &s_dropegg }, { SND_DAC, &s_dropfood }, { SND_DAC, &s_droprock }, { SND_DAC, &s_fooddrip },
    { SND_DAC, &s_foodslop }, { SND_DAC, &s_foodunsl }, { SND_DAC, &s_humanfoo }, { SND_DAC, &s_kick },
    { SND_DAC, &s_lawnmowr }, { SND_DAC, &s_lioncrun }, { SND_DAC, &s_lionroar }, { SND_DAC, &s_lionsnar },
    { SND_DAC, &s_pop }, { SND_DAC, &s_rain }, { SND_DAC, &s_retch }, { SND_DAC, &s_shaker },
    { SND_DAC, &s_slurp }, { SND_DAC, &s_slurplng }, { SND_DAC, &s_kick }, { SND_DAC, &s_spiderft },
    { SND_DAC, &s_kick }, { SND_DAC, &s_tearing }, { SND_DAC, &s_kick }, { SND_DAC, &s_kick },
    { SND_DAC, &s_whistle }, { SND_DAC, &s_square4 }, { SND_DAC, &s_square3 }
};

PortableWholeAudioInstrumentEntry fd_55B3_0D92[56] = {
    { SND_FM, &fm09 }, { SND_DAC, &s_alert1 }, { SND_DAC, &s_alert2 }, { SND_FM, &fm07 },
    { SND_DAC, &s_beep1 }, { SND_DAC, &s_beep2 }, { SND_DAC, &s_beep3 }, { SND_DAC, &s_birdcall },
    { SND_DAC, &s_brasssyn }, { SND_FM, &fm19 }, { SND_DAC, &s_burp }, { SND_DAC, &s_buzzing },
    { SND_DAC, &s_beep2 }, { SND_DAC, &s_catmeow }, { SND_DAC, &s_catyowl }, { SND_FM, &fm01 },
    { SND_FM, &fm01 }, { SND_FM, &fm02 }, { SND_FM, &fm03 }, { SND_FM, &fm04 },
    { SND_DAC, &s_dogfoot }, { SND_DAC, &s_dogwhim1 }, { SND_DAC, &s_dogwhim2 }, { SND_DAC, &s_dogyap },
    { SND_DAC, &s_doorslam }, { SND_FM, &fm08 }, { SND_DAC, &s_drip1 }, { SND_DAC, &s_drip2 },
    { SND_DAC, &s_dropegg }, { SND_DAC, &s_dropfood }, { SND_FM, &fm05 }, { SND_DAC, &s_fooddrip },
    { SND_DAC, &s_foodslop }, { SND_DAC, &s_foodunsl }, { SND_DAC, &s_humanfoo }, { SND_FM, &fm14 },
    { SND_DAC, &s_lawnmowr }, { SND_DAC, &s_lioncrun }, { SND_DAC, &s_lionroar }, { SND_DAC, &s_lionsnar },
    { SND_DAC, &s_pop }, { SND_DAC, &s_rain }, { SND_DAC, &s_retch }, { SND_DAC, &s_beep2 },
    { SND_DAC, &s_slurp }, { SND_DAC, &s_slurplng }, { SND_FM, &fm11 }, { SND_DAC, &s_spiderft },
    { SND_FM, &fm12 }, { SND_DAC, &s_tearing }, { SND_FM, &fm15 }, { SND_FM, &fm13 },
    { SND_DAC, &s_beep2 }, { SND_FM, &fm10 }, { SND_FM, &fm10 }
};

PortableWholeAudioInstrumentEntry fd_55B3_0EE2[56] = {
    { SND_DAC, &s_agogo }, { SND_DAC, &s_alert1 }, { SND_DAC, &s_alert2 }, { SND_DAC, &s_bassass },
    { SND_DAC, &s_beep1 }, { SND_DAC, &s_beep2 }, { SND_DAC, &s_beep3 }, { SND_DAC, &s_birdcall },
    { SND_DAC, &s_brasssyn }, { SND_DAC, &s_bugspray }, { SND_DAC, &s_burp }, { SND_DAC, &s_buzzing },
    { SND_DAC, &s_cabasa }, { SND_DAC, &s_catmeow }, { SND_DAC, &s_catyowl }, { SND_DAC, &s_click },
    { SND_DAC, &s_click2 }, { SND_DAC, &s_dig1 }, { SND_DAC, &s_dig2 }, { SND_DAC, &s_dig3 },
    { SND_DAC, &s_dogfoot }, { SND_DAC, &s_dogwhim1 }, { SND_DAC, &s_dogwhim2 }, { SND_DAC, &s_dogyap },
    { SND_DAC, &s_doorslam }, { SND_DAC, &s_dreamgui }, { SND_DAC, &s_drip1 }, { SND_DAC, &s_drip2 },
    { SND_DAC, &s_dropegg }, { SND_DAC, &s_dropfood }, { SND_DAC, &s_droprock }, { SND_DAC, &s_fooddrip },
    { SND_DAC, &s_foodslop }, { SND_DAC, &s_foodunsl }, { SND_DAC, &s_humanfoo }, { SND_DAC, &s_kick },
    { SND_DAC, &s_lawnmowr }, { SND_DAC, &s_lioncrun }, { SND_DAC, &s_lionroar }, { SND_DAC, &s_lionsnar },
    { SND_DAC, &s_pop }, { SND_DAC, &s_rain }, { SND_DAC, &s_retch }, { SND_DAC, &s_shaker },
    { SND_DAC, &s_slurp }, { SND_DAC, &s_slurplng }, { SND_DAC, &s_snare }, { SND_DAC, &s_spiderft },
    { SND_DAC, &s_stick }, { SND_DAC, &s_tearing }, { SND_DAC, &s_tom }, { SND_DAC, &s_whap },
    { SND_DAC, &s_whistle }, { SND_DAC, &s_keys }, { SND_DAC, &s_ooohs }
};

PortableWholeAudioInstrumentEntry fd_55B3_1032[56] = {
    { SND_DAC, &s_kick }, { SND_DAC, &s_alert1 }, { SND_DAC, &s_alert2 }, { SND_PSG5, 0 },
    { SND_DAC, &s_beep1 }, { SND_DAC, &s_beep2 }, { SND_DAC, &s_beep3 }, { SND_DAC, &s_birdcall },
    { SND_DAC, &s_brasssyn }, { SND_DAC, &s_bugspray }, { SND_DAC, &s_burp }, { SND_DAC, &s_buzzing },
    { SND_DAC, &s_cabasa }, { SND_DAC, &s_catmeow }, { SND_DAC, &s_catyowl }, { SND_DAC, &s_kick },
    { SND_DAC, &s_kick }, { SND_DAC, &s_kick }, { SND_DAC, &s_dig2 }, { SND_DAC, &s_dig3 },
    { SND_DAC, &s_dogfoot }, { SND_DAC, &s_dogwhim1 }, { SND_DAC, &s_dogwhim2 }, { SND_DAC, &s_dogyap },
    { SND_DAC, &s_doorslam }, { SND_PSG5, 0 }, { SND_DAC, &s_drip1 }, { SND_DAC, &s_drip2 },
    { SND_DAC, &s_dropegg }, { SND_DAC, &s_dropfood }, { SND_DAC, &s_droprock }, { SND_DAC, &s_fooddrip },
    { SND_DAC, &s_foodslop }, { SND_DAC, &s_foodunsl }, { SND_DAC, &s_humanfoo }, { SND_DAC, &s_kick },
    { SND_DAC, &s_lawnmowr }, { SND_DAC, &s_lioncrun }, { SND_DAC, &s_lionroar }, { SND_DAC, &s_lionsnar },
    { SND_DAC, &s_pop }, { SND_DAC, &s_rain }, { SND_DAC, &s_retch }, { SND_DAC, &s_shaker },
    { SND_DAC, &s_slurp }, { SND_DAC, &s_slurplng }, { SND_DAC, &s_kick }, { SND_DAC, &s_spiderft },
    { SND_DAC, &s_kick }, { SND_DAC, &s_tearing }, { SND_DAC, &s_kick }, { SND_DAC, &s_kick },
    { SND_DAC, &s_whistle }, { SND_PSG5, 0 }, { SND_PSG5, 0 }
};

PortableWholeAudioInstrumentEntry fd_55B3_1182[56] = {
    { SND_DAC, &s_agogo }, { SND_DAC, &s_alert1 }, { SND_DAC, &s_alert2 }, { SND_PSG5, 0 },
    { SND_DAC, &s_beep1 }, { SND_DAC, &s_beep2 }, { SND_DAC, &s_beep3 }, { SND_DAC, &s_birdcall },
    { SND_DAC, &s_brasssyn }, { SND_DAC, &s_bugspray }, { SND_DAC, &s_burp }, { SND_DAC, &s_buzzing },
    { SND_DAC, &s_cabasa }, { SND_DAC, &s_catmeow }, { SND_DAC, &s_catyowl }, { SND_DAC, &s_click },
    { SND_DAC, &s_click2 }, { SND_DAC, &s_dig1 }, { SND_DAC, &s_dig2 }, { SND_DAC, &s_dig3 },
    { SND_DAC, &s_dogfoot }, { SND_DAC, &s_dogwhim1 }, { SND_DAC, &s_dogwhim2 }, { SND_DAC, &s_dogyap },
    { SND_DAC, &s_doorslam }, { SND_PSG5, 0 }, { SND_DAC, &s_drip1 }, { SND_DAC, &s_drip2 },
    { SND_DAC, &s_dropegg }, { SND_DAC, &s_dropfood }, { SND_DAC, &s_droprock }, { SND_DAC, &s_fooddrip },
    { SND_DAC, &s_foodslop }, { SND_DAC, &s_foodunsl }, { SND_DAC, &s_humanfoo }, { SND_DAC, &s_kick },
    { SND_DAC, &s_lawnmowr }, { SND_DAC, &s_lioncrun }, { SND_DAC, &s_lionroar }, { SND_DAC, &s_lionsnar },
    { SND_DAC, &s_pop }, { SND_DAC, &s_rain }, { SND_DAC, &s_retch }, { SND_DAC, &s_shaker },
    { SND_DAC, &s_slurp }, { SND_DAC, &s_slurplng }, { SND_DAC, &s_snare }, { SND_DAC, &s_spiderft },
    { SND_DAC, &s_stick }, { SND_DAC, &s_tearing }, { SND_DAC, &s_tom }, { SND_DAC, &s_whap },
    { SND_DAC, &s_whistle }, { SND_PSG5, 0 }, { SND_PSG5, 0 }
};

PortableWholeAudioInstrumentEntry fd_55B3_12D2[56] = {
    { SND_MIDI, midiMap[0] }, { SND_DAC, &s_alert1 }, { SND_DAC, &s_alert2 }, { SND_MIDI, midiMap[3] },
    { SND_MIDI, midiMap[4] }, { SND_MIDI, midiMap[5] }, { SND_MIDI, midiMap[6] }, { SND_MIDI, midiMap[7] },
    { SND_DAC, &s_brasssyn }, { SND_DAC, &s_bugspray }, { SND_DAC, &s_burp }, { SND_DAC, &s_buzzing },
    { SND_MIDIDRUM, midiMap[12] }, { SND_DAC, &s_catmeow }, { SND_DAC, &s_catyowl }, { SND_MIDIDRUM, midiMap[15] },
    { SND_MIDIDRUM, midiMap[15] }, { SND_MIDIDRUM, midiMap[17] }, { SND_MIDIDRUM, midiMap[17] }, { SND_MIDIDRUM, midiMap[17] },
    { SND_DAC, &s_dogfoot }, { SND_DAC, &s_dogwhim1 }, { SND_DAC, &s_dogwhim2 }, { SND_DAC, &s_dogyap },
    { SND_DAC, &s_doorslam }, { SND_MIDI, midiMap[25] }, { SND_DAC, &s_drip1 }, { SND_DAC, &s_drip2 },
    { SND_MIDIDRUM, midiMap[17] }, { SND_MIDIDRUM, midiMap[18] }, { SND_MIDIDRUM, midiMap[19] }, { SND_DAC, &s_fooddrip },
    { SND_DAC, &s_foodslop }, { SND_DAC, &s_foodunsl }, { SND_DAC, &s_humanfoo }, { SND_MIDIDRUM, midiMap[35] },
    { SND_DAC, &s_lawnmowr }, { SND_DAC, &s_lioncrun }, { SND_DAC, &s_lionroar }, { SND_DAC, &s_lionsnar },
    { SND_DAC, &s_pop }, { SND_MIDIDRUM, midiMap[41] }, { SND_DAC, &s_retch }, { SND_DAC, &s_shaker },
    { SND_DAC, &s_slurp }, { SND_DAC, &s_slurplng }, { SND_MIDI, midiMap[46] }, { SND_DAC, &s_spiderft },
    { SND_MIDIDRUM, midiMap[48] }, { SND_DAC, &s_tearing }, { SND_MIDI, midiMap[50] }, { SND_MIDIDRUM, midiMap[51] },
    { SND_MIDI, midiMap[52] }, { SND_MIDI, midiMap[53] }, { SND_MIDI, midiMap[53] }
};

PortableWholeAudioInstrumentEntry fd_55B3_1422[56] = {
    { SND_MIDI, midiMap[0] }, { SND_DAC, &s_alert1 }, { SND_DAC, &s_alert2 }, { SND_MIDI, midiMap[3] },
    { SND_DAC, &s_beep1 }, { SND_DAC, &s_beep2 }, { SND_DAC, &s_beep3 }, { SND_DAC, &s_birdcall },
    { SND_DAC, &s_brasssyn }, { SND_DAC, &s_bugspray }, { SND_DAC, &s_burp }, { SND_DAC, &s_buzzing },
    { SND_MIDIDRUM, midiMap[12] }, { SND_DAC, &s_catmeow }, { SND_DAC, &s_catyowl }, { SND_DAC, &s_click },
    { SND_DAC, &s_click }, { SND_DAC, &s_dig1 }, { SND_DAC, &s_dig2 }, { SND_DAC, &s_dig3 },
    { SND_DAC, &s_dogfoot }, { SND_DAC, &s_dogwhim1 }, { SND_DAC, &s_dogwhim2 }, { SND_DAC, &s_dogyap },
    { SND_DAC, &s_doorslam }, { SND_MIDI, midiMap[25] }, { SND_DAC, &s_drip1 }, { SND_DAC, &s_drip2 },
    { SND_DAC, &s_dropegg }, { SND_DAC, &s_dropfood }, { SND_DAC, &s_droprock }, { SND_DAC, &s_fooddrip },
    { SND_DAC, &s_foodslop }, { SND_DAC, &s_foodunsl }, { SND_DAC, &s_humanfoo }, { SND_MIDIDRUM, midiMap[35] },
    { SND_DAC, &s_lawnmowr }, { SND_DAC, &s_lioncrun }, { SND_DAC, &s_lionroar }, { SND_DAC, &s_lionsnar },
    { SND_DAC, &s_pop }, { SND_DAC, &s_rain }, { SND_DAC, &s_retch }, { SND_DAC, &s_shaker },
    { SND_DAC, &s_slurp }, { SND_DAC, &s_slurplng }, { SND_MIDI, midiMap[46] }, { SND_DAC, &s_spiderft },
    { SND_MIDIDRUM, midiMap[48] }, { SND_DAC, &s_tearing }, { SND_MIDI, midiMap[50] }, { SND_MIDIDRUM, midiMap[51] },
    { SND_MIDI, midiMap[52] }, { SND_MIDI, midiMap[53] }, { SND_MIDI, midiMap[53] }
};

PortableWholeAudioInstrumentEntry fd_55B3_1572[56] = {
    { SND_DAC, &s_agogo }, { SND_DAC, &s_alert1 }, { SND_DAC, &s_alert2 }, { SND_PSG4, 0 },
    { SND_DAC, &s_beep1 }, { SND_DAC, &s_beep2 }, { SND_DAC, &s_beep3 }, { SND_DAC, &s_birdcall },
    { SND_DAC, &s_brasssyn }, { SND_DAC, &s_bugspray }, { SND_DAC, &s_burp }, { SND_DAC, &s_buzzing },
    { SND_DAC, &s_cabasa }, { SND_DAC, &s_catmeow }, { SND_DAC, &s_catyowl }, { SND_DAC, &s_click },
    { SND_DAC, &s_click2 }, { SND_DAC, &s_dig1 }, { SND_DAC, &s_dig2 }, { SND_DAC, &s_dig3 },
    { SND_DAC, &s_dogfoot }, { SND_DAC, &s_dogwhim1 }, { SND_DAC, &s_dogwhim2 }, { SND_DAC, &s_dogyap },
    { SND_DAC, &s_doorslam }, { SND_PSG4, 0 }, { SND_DAC, &s_drip1 }, { SND_DAC, &s_drip2 },
    { SND_DAC, &s_dropegg }, { SND_DAC, &s_dropfood }, { SND_DAC, &s_droprock }, { SND_DAC, &s_fooddrip },
    { SND_DAC, &s_foodslop }, { SND_DAC, &s_foodunsl }, { SND_DAC, &s_humanfoo }, { SND_DAC, &s_kick },
    { SND_DAC, &s_lawnmowr }, { SND_DAC, &s_lioncrun }, { SND_DAC, &s_lionroar }, { SND_DAC, &s_lionsnar },
    { SND_DAC, &s_pop }, { SND_DAC, &s_rain }, { SND_DAC, &s_retch }, { SND_DAC, &s_shaker },
    { SND_DAC, &s_slurp }, { SND_DAC, &s_slurplng }, { SND_DAC, &s_snare }, { SND_DAC, &s_spiderft },
    { SND_DAC, &s_stick }, { SND_DAC, &s_tearing }, { SND_DAC, &s_tom }, { SND_DAC, &s_whap },
    { SND_DAC, &s_whistle }, { SND_PSG4, 0 }, { SND_PSG4, 0 }
};

PortableWholeAudioInstrumentEntry fd_55B3_16C2[56] = {
    { SND_DAC, &s_agogo }, { SND_DAC, &s_alert1 }, { SND_DAC, &s_alert2 }, { SND_PSG3, 0 },
    { SND_DAC, &s_beep1 }, { SND_DAC, &s_beep2 }, { SND_DAC, &s_beep3 }, { SND_DAC, &s_birdcall },
    { SND_DAC, &s_brasssyn }, { SND_DAC, &s_bugspray }, { SND_DAC, &s_burp }, { SND_DAC, &s_buzzing },
    { SND_DAC, &s_cabasa }, { SND_DAC, &s_catmeow }, { SND_DAC, &s_catyowl }, { SND_DAC, &s_click },
    { SND_DAC, &s_click2 }, { SND_DAC, &s_dig1 }, { SND_DAC, &s_dig2 }, { SND_DAC, &s_dig3 },
    { SND_DAC, &s_dogfoot }, { SND_DAC, &s_dogwhim1 }, { SND_DAC, &s_dogwhim2 }, { SND_DAC, &s_dogyap },
    { SND_DAC, &s_doorslam }, { SND_PSG3, 0 }, { SND_DAC, &s_drip1 }, { SND_DAC, &s_drip2 },
    { SND_DAC, &s_dropegg }, { SND_DAC, &s_dropfood }, { SND_DAC, &s_droprock }, { SND_DAC, &s_fooddrip },
    { SND_DAC, &s_foodslop }, { SND_DAC, &s_foodunsl }, { SND_DAC, &s_humanfoo }, { SND_DAC, &s_kick },
    { SND_DAC, &s_lawnmowr }, { SND_DAC, &s_lioncrun }, { SND_DAC, &s_lionroar }, { SND_DAC, &s_lionsnar },
    { SND_DAC, &s_pop }, { SND_DAC, &s_rain }, { SND_DAC, &s_retch }, { SND_DAC, &s_shaker },
    { SND_DAC, &s_slurp }, { SND_DAC, &s_slurplng }, { SND_DAC, &s_snare }, { SND_DAC, &s_spiderft },
    { SND_DAC, &s_stick }, { SND_DAC, &s_tearing }, { SND_DAC, &s_tom }, { SND_DAC, &s_whap },
    { SND_DAC, &s_whistle }, { SND_PSG3, 0 }, { SND_PSG3, 0 }
};

#pragma pack(pop)
