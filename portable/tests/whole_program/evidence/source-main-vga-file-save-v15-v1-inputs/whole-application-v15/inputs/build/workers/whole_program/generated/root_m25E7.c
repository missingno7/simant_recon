#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "portable/whole_program/types/fonts.h"
#pragma pack(push, 2)
/* Root module 25E7: bitmap fonts (Macintosh FONT layout, byte-swapped on load). */





extern int16_t g_6740;
extern int16_t g_673E;

int16_t g_673E = 80;
int16_t g_6740 = 16;


void  f_25E7_0008(int16_t  *p, int16_t count, DosFileStream  *fp)
{
    int16_t w;
    int16_t i;
    uint8_t ch1;
    uint8_t ch2;

    dos_fread(p, count, 2, fp);
    for (i = 0; i < count; i++) {
        w = *p;
        ch1 = ((uint8_t *)&w)[0];
        ch2 = ((uint8_t *)&w)[1];
        w = (ch1 << 8) | ch2;
        *p++ = w;
    }
}

extern char  *  f_171C_2190(uint16_t size, char  *name);

extern void  dos_free(void  *p);


int16_t  _font_StringWidth(uint8_t  *s, struct Font  *font);

struct Font  *  font_ReadFont(char  *name)
{
    DosFileStream  *fp;
    struct Font  *font;
    int16_t count;
    int16_t size;

    font = (struct Font  *)f_171C_2190(sizeof(struct Font), "FontHeader");
    if (font == 0)
        return 0;
    fp = dos_fopen(name, "rb");
    if (fp == 0) {
        dos_free(font);
        return 0;
    }
    f_25E7_0008((int16_t  *)font, 13, fp);
    if (font->fRectHeight > g_6740) {
        dos_free(font);
        return 0;
    }
    count = font->lastChar - font->firstChar + 3;
    size = font->rowWords * font->fRectHeight * 2;
    font->image = f_171C_2190(size, "FONTIMAGE");
    font->locTable = (int16_t  *)f_171C_2190(count * 2, "locTable");
    font->owTable = (int16_t  *)f_171C_2190(count * 2, "owTable");
    dos_fread(font->image, size, 1, fp);
    f_25E7_0008(font->locTable, count, fp);
    f_25E7_0008(font->owTable, count, fp);
    dos_fclose(fp);
    font->proportional = (font->fontType & 0x2000) == 0;
    font->missing = font->lastChar - font->firstChar + 1;
    return font;
}

struct Font  *  font_DumpFont(struct Font  *font)
{
    if (font == 0)
        return 0;
    if (font->image)
        dos_free(font->image);
    if (font->locTable)
        dos_free(font->locTable);
    if (font->owTable)
        dos_free(font->owTable);
    if (font)
        dos_free(font);
    return 0;
}




extern struct Bitmap  fd_50F6_392C;
extern void  f_2650_0107(char  *buf, int16_t size);
extern int16_t  fd_55B3_6770;
extern int16_t  fd_55B3_6772;
extern void  f_2650_000F(char  *, char  *, int16_t, int16_t, int16_t, int16_t);

int16_t  _font_StringWidth(uint8_t  *s, struct Font  *font)
{
    char c;
    int16_t extra;
    int16_t i;
    int16_t result;

    i = 0;
    result = 0;
    if (font->proportional) {
        if (font->kernMax < 0)
            extra = 1;
        else
            extra = 0;
        while (s[i]) {
            if (font->owTable[s[i]] != -1) {
                result += (uint8_t)font->owTable[s[i]];
                i++;
            } else {
                result += (uint8_t)font->owTable[font->missing];
                i++;
            }
            result += extra;
        }
    } else {
        result = _fstrlen(s) * font->widMax;
    }
    return result;
}

int16_t  _font_CharWidth(int16_t ch, struct Font  *font)
{
    int16_t extra;
    int16_t i;
    int16_t result;

    i = 0;
    result = 0;
    ch &= 0xff;
    if (font->proportional) {
        if (font->kernMax < 0)
            extra = 1;
        else
            extra = 0;
        if (font->owTable[ch] != -1)
            result += (uint8_t)font->owTable[ch];
        else
            result += (uint8_t)font->owTable[font->missing];
        result += extra;
    } else {
        result = font->widMax;
    }
    return result;
}

int16_t  _font_FontHeight(struct Font  *font)
{
    return font->fRectHeight - 1;
}

int16_t  _font_LineHeight(struct Font  *font)
{
    return font->leading + font->fRectHeight - 1;
}

struct Bitmap  *  font_MakeImage(uint8_t  *s, int16_t x, struct Font  *font)
{
     int16_t i;
    int16_t xofs;
    int16_t width;
    int16_t edge;
    int16_t pen;
    int16_t glyphWidth;
    int16_t kk;
    uint8_t ch;
    int16_t sx;

    i = 0;
    pen = x;
    width = font->widMax;
    f_2650_0107(fd_50F6_392C.bits, g_673E * g_6740);
    fd_55B3_6770 = font->rowWords * 2;
    fd_55B3_6772 = (_font_StringWidth(s, font) + x + 7) >> 3;
    fd_50F6_392C.height = font->fRectHeight;
    edge = (g_673E << 3) - font->fRectWidth;
    for (i = 0; s[i] && pen < edge; i++) {
        ch = s[i];
        if (font->owTable[ch] == -1)
            ch = (uint8_t)font->missing;
        kk = (uint16_t)font->owTable[ch] >> 8;
        if (font->proportional)
            width = (uint8_t)font->owTable[ch];
        sx = font->locTable[ch];
        glyphWidth = font->locTable[ch + 1] - sx;
        if (font->kernMax < 0) {
            xofs = 0;
            width++;
        } else {
            xofs = font->kernMax + kk;
        }
        f_2650_000F(font->image + fd_55B3_6770, fd_50F6_392C.bits, glyphWidth, font->fRectHeight - 1, sx, pen + xofs);
        pen += width;
    }
    fd_50F6_392C.width = pen;
    fd_50F6_392C.height--;
    return &fd_50F6_392C;
}

#pragma pack(pop)
