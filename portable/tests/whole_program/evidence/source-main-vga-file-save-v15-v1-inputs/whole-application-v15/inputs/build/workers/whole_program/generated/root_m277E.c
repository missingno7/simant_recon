#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/platform/audio_state.h"
#include "portable/whole_program/platform/audio.h"
#pragma pack(push, 2)

/* Root module 277E: sound device selection and channel tables. */





int16_t  f_277E_0179(void);
int16_t  f_277E_017D(void);
int16_t  f_277E_01FA(void);
int16_t  f_277E_034F(void);
int16_t  f_277E_040E(void);
int16_t  f_277E_04E8(void);
int16_t  f_277E_0606(void);
int16_t  f_277E_0760(void);
int16_t  f_277E_07FF(void);
void  f_277E_0938(void);
void  f_277E_0939(void);
void  f_277E_0952(void);
void  f_277E_0958(void);
void  f_277E_0965(void);

int16_t ( *g_68B6[])(void) = {
    f_277E_0179, f_277E_017D, f_277E_01FA, f_277E_034F, f_277E_040E,
    f_277E_0606, f_277E_04E8, f_277E_0760, f_277E_07FF
};

void ( *g_68DA[])(void) = {
    f_277E_0938, f_277E_0958, f_277E_0938, f_277E_0938, f_277E_0938,
    f_277E_0965, f_277E_0939, f_277E_0952, f_277E_0938
};

extern char g_68FE[];
extern char g_6908[];
extern char g_6912[];
extern int16_t g_6924[];
extern int16_t g_693C;


void  f_277E_00AF(void);
extern void  f_29F0_001A(void);
extern int16_t  fd_50F6_4A48;
extern int16_t  fd_50F6_4A4C;
extern void  f_28BC_046B(int16_t a, int16_t b);
extern void  f_28BC_0488(int16_t a, int16_t b);
extern void  f_28BC_03CC(void);
extern void  f_29F0_0022(void);

extern int16_t  f_0000_0000(char  *  *handle, int16_t  *size, int16_t object, int16_t type);
extern void  f_19A9_000B(int16_t ( *hook)(char  *  *handle, int16_t  *size, int16_t object, int16_t type));

int16_t  f_277E_0000(int16_t mode, int16_t flag)
{
    if (mode != 7 && !fd_55B3_74DA[mode]())
        mode = 1;
    f_277E_00AF();
    f_29F0_001A();
    fd_50F6_4A48 = 2;
    if (mode == 7)
        flag = 1;
    if (flag)
        fd_50F6_4A48 = 4;
    fd_50F6_4A4C = 0;
    g_68B6[mode]();
    if (flag)
        f_28BC_046B(0xd6, 0x132);
    else
        f_28BC_0488(0xd6, 0x132);
    f_28BC_03CC();
    f_29F0_0022();
    fd_50F6_01F0[0] = mode;
    f_19A9_000B(f_0000_0000);
    return mode;
}



void  f_277E_00AF(void)
{
    int16_t i;

    for (i = 0; i < 0x21; i++) {
        fd_50F6_4A4E[i].type = 0;
        fd_50F6_4A4E[i].num = 0;
        fd_50F6_4A4E[i].c4 = 0;
        fd_50F6_4A4E[i].c5 = 15;
        fd_50F6_4A4E[i].c2 = 0;
        fd_50F6_4A4E[i].c3 = -1;
    }
    fd_50F6_01F0[1] = 0;
    fd_50F6_01F0[2] = 0;
    fd_50F6_01F0[3] = 0;
    fd_50F6_01F0[4] = 0;
    fd_50F6_01F0[5] = 0;
    fd_50F6_01F0[6] = 0;
}



void  f_277E_010A(PortableWholeAudioInstrumentEntry  *src)
{
    int16_t i;

    for (i = 0; i < 0x38; i++) {
        fd_50F6_0000[i].kind = src[i].kind;
        fd_50F6_0000[i].payload = src[i].payload;
    }
}

extern void  f_295C_0391(void);
extern void  f_0000_0429(void);
extern void  f_28BC_04E0(int16_t a);

void  f_277E_0154(void)
{
    f_295C_0391();
    f_0000_0429();
    g_68DA[fd_50F6_01F0[0]]();
    f_28BC_04E0(0);
}

int16_t  f_277E_0179(void)
{
    return 1;
}




extern PortableWholeAudioInstrumentEntry  fd_55B3_0C42[];

int16_t  f_277E_017D(void)
{
    int16_t i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    fd_55B3_6B9C = fd_55B3_74AD;
    fd_55B3_74C0 = 0x40;
    f_277E_010A(fd_55B3_0C42);
    return 1;
}

extern int16_t  fd_50F6_4A4A;
extern int16_t  fd_50F6_4B14;

extern void  f_29F0_002A(int16_t port, char value);


extern PortableWholeAudioInstrumentEntry  fd_55B3_1032[];
extern PortableWholeAudioInstrumentEntry  fd_55B3_1182[];
int16_t  f_277E_01FA(void)
{
    int16_t i;
    int16_t base;
    uint8_t bios_signature;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    fd_50F6_4A4A = fd_55B3_74C0 = 0;
    base = 0xc4;
    {
        uint16_t ax = dos_audio_host_bios_int1a_8100();
        if (ax == 0x00c4)
            base = (int16_t)ax;
    }
    fd_50F6_4A4A = 0;
    for (i = 0; i < 3; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 5;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    fd_50F6_01F0[4] = 3;
    bios_signature = dos_audio_host_read_far_u8(0xf000, 0xfffe);
    if (bios_signature == 0xfc)
        fd_50F6_4B14 = 0x1e0;
    else
        fd_50F6_4B14 = 0xc0;
    if (fd_50F6_4A4A) {
        f_29F0_002A(fd_55B3_6B4A = base, 3);
        fd_55B3_6B9C = fd_55B3_74B9;
        f_277E_010A(fd_55B3_1182);
    } else {
        fd_55B3_6B9C = fd_55B3_74AD;
        f_277E_010A(fd_55B3_1032);
    }
    return 1;
}



int16_t  f_277E_034F(void)
{
    int16_t i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    for (i = 0; i < 3; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 3;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    fd_50F6_01F0[3] = 3;
    f_29F0_002A(0x203, 1);
    fd_55B3_6B9C = fd_55B3_74B3;
    fd_55B3_74C0 = 0;
    return 1;
}

extern void  f_2815_0118(void);
extern void  f_283E_0035(void);



extern PortableWholeAudioInstrumentEntry  fd_55B3_0D92[];
int16_t  f_277E_040E(void)
{
    int16_t i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    for (i = 0; i < 7; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 2;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i + 1;
    }
    f_2815_0118();
    fd_50F6_01F0[2] = 7;
    f_283E_0035();
    f_29F0_001A();
    fd_55B3_6B9C = fd_55B3_74AF;
    f_277E_010A(fd_55B3_0D92);
    fd_50F6_4B16 = -40;
    fd_55B3_74C0 = 0x60;
    return 1;
}


extern int16_t  f_293A_0121(void);

extern uint8_t  f_29F0_0038(int16_t port);


int16_t  f_277E_04E8(void)
{
    uint16_t i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    f_2815_0118();
    for (i = 0; i < 8; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 2;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    fd_50F6_01F0[2] = 8;
    fd_55B3_74C0 = -10;
    if (fd_55B3_7564 < 0x210) {
        f_293A_0121();
        fd_55B3_6BA0 = fd_55B3_7564 + 12;
        while (f_29F0_0038(fd_55B3_6BA0) & 0x80)
            ;
    }
    fd_55B3_6BA0 = fd_55B3_7564 + 12;
    fd_55B3_6B9C = fd_55B3_74B5;
    f_277E_010A(fd_55B3_0D92);
    f_29F0_002A(fd_55B3_6BA0, 0xd1);
    return 1;
}

extern void  f_293A_015E(void);
extern int16_t  fd_50F6_4A46;
extern int16_t  f_293A_0087(void);

extern void  f_29BF_0008(int16_t port);

extern PortableWholeAudioInstrumentEntry  fd_55B3_1572[];
int16_t  f_277E_0606(void)
{
    int16_t i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    for (i = 0; i < 3; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 4;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    fd_50F6_01F0[5] = 3;
    if (fd_50F6_4B14 == 0)
        f_293A_015E();
    if (fd_50F6_4B14 == 0)
        fd_50F6_4B14 = 0x220;
    fd_50F6_4A46 = fd_50F6_4B14 + 2;
    if (f_293A_0087()) {
        f_277E_010A(fd_55B3_0D92);
        f_2815_0118();
        for (i = 0; i < 8; i++, fd_50F6_4A4C++) {
            fd_50F6_4A4E[fd_50F6_4A4C].type = 2;
            fd_50F6_4A4E[fd_50F6_4A4C].num = i;
        }
        fd_50F6_01F0[2] = 8;
    } else
        f_277E_010A(fd_55B3_1572);
    fd_55B3_6B9C = fd_55B3_74B7;
    f_29BF_0008(fd_50F6_4B14);
    fd_55B3_74C0 = 0;
    return 1;
}



extern PortableWholeAudioInstrumentEntry  fd_55B3_0EE2[];
int16_t  f_277E_0760(void)
{
    int16_t i;

    fd_50F6_01F0[1] = fd_50F6_4A48;
    for (i = 0; i < fd_50F6_4A48; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 1;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i;
    }
    {
        uint16_t dx;
        uint8_t value;
        g_693C = (int16_t)dos_audio_host_read_far_u16(0x0040, 0x0008);
        dx = (uint16_t)(g_693C + 2);
        value = dos_audio_host_in8(dx);
        dos_audio_host_out8(dx, (uint8_t)(value & 0xf7));
    }
    fd_55B3_6B9C = fd_55B3_74B1;
    f_277E_010A(fd_55B3_0EE2);
    fd_55B3_74C0 = 0;
    return 1;
}

extern void  f_295C_03FF(int16_t c);
extern void  f_295C_03DC(int16_t c);

extern PortableWholeAudioInstrumentEntry  fd_55B3_12D2[];
extern PortableWholeAudioInstrumentEntry  fd_55B3_1422[];
int16_t  f_277E_07FF(void)
{
    int16_t i;

    fd_50F6_01F0[6] = 8;
    if (f_293A_0121()) {
        f_277E_04E8();
        f_277E_010A(fd_55B3_1422);
    } else {
        f_277E_017D();
        f_277E_010A(fd_55B3_12D2);
    }
    fd_55B3_74C0 = 0;
    for (i = 0; i < 8; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 6;
        fd_50F6_4A4E[fd_50F6_4A4C].num = i + 1;
    }
    for (i = 0; i < 10; i++, fd_50F6_4A4C++) {
        fd_50F6_4A4E[fd_50F6_4A4C].type = 7;
        fd_50F6_4A4E[fd_50F6_4A4C].num = 10;
    }
    f_295C_03FF(0x8a);
    f_295C_03FF(0xd7);
    for (i = 0; i < 16; i++) {
        f_295C_03FF(0xd7);
        f_295C_03DC(i + 0xb0);
        f_295C_03DC(0x79);
        f_295C_03DC(0);
        f_295C_03DC(i + 0xb0);
        f_295C_03DC(0x7b);
        f_295C_03DC(0);
        f_295C_03DC(i + 0xb0);
        f_295C_03DC(10);
        f_295C_03DC(0x40);
        f_295C_03DC(i + 0xb0);
        f_295C_03DC(7);
        f_295C_03DC(0x7f);
    }
    return 1;
}

void  f_277E_0938(void)
{
}

void  f_277E_0939(void)
{
    f_29F0_002A(fd_55B3_6BA0, 0xd3);
    f_2815_0118();
}

void  f_277E_0952(void)
{
    f_2815_0118();
}

void  f_277E_0958(void)
{
    {
        uint8_t value = dos_audio_host_in8(0x0061);
        dos_audio_host_out8(0x0061, (uint8_t)(value & 0xfc));
    }
}

void  f_277E_0965(void)
{
    dos_audio_host_out8(0x000a, 0x05);
    dos_audio_host_out8(0x0220, 0x0f);
    dos_audio_host_out8(0x0221, 0x60);
}

#pragma pack(pop)
