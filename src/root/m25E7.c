/* Root module 25E7: bitmap fonts (Macintosh FONT layout, byte-swapped on load). */

typedef struct _iobuf FILE;

struct Font {
    int fontType;
    int firstChar;
    int lastChar;
    int widMax;
    int kernMax;
    int nDescent;
    int fRectWidth;
    int fRectHeight;
    int owTLoc;
    int ascent;
    int descent;
    int leading;
    int rowWords;
    char far *image;
    int far *locTable;
    int far *owTable;
    int proportional;
    int missing;
};

extern int g_6740;
extern int g_673E;

int g_673E = 80;
int g_6740 = 16;

extern unsigned far fread(void far *buf, unsigned size, unsigned count, FILE far *fp);

void far f_25E7_0008(int far *p, int count, FILE far *fp)
{
    int w;
    int i;
    unsigned char ch1;
    unsigned char ch2;

    fread(p, count, 2, fp);
    for (i = 0; i < count; i++) {
        w = *p;
        ch1 = ((unsigned char *)&w)[0];
        ch2 = ((unsigned char *)&w)[1];
        w = (ch1 << 8) | ch2;
        *p++ = w;
    }
}

extern char far * far f_171C_2190(unsigned size, char far *name);
extern FILE far * far fopen(char far *name, char far *mode);
extern void far f_171C_2276(void far *p);
extern int far fclose(FILE far *fp);

int far _font_StringWidth(unsigned char far *s, struct Font far *font);

struct Font far * far font_ReadFont(char far *name)
{
    FILE far *fp;
    struct Font far *font;
    int count;
    int size;

    font = (struct Font far *)f_171C_2190(0x2a, "FontHeader");
    if (font == 0)
        return 0;
    fp = fopen(name, "rb");
    if (fp == 0) {
        f_171C_2276(font);
        return 0;
    }
    f_25E7_0008((int far *)font, 13, fp);
    if (font->fRectHeight > g_6740) {
        f_171C_2276(font);
        return 0;
    }
    count = font->lastChar - font->firstChar + 3;
    size = font->rowWords * font->fRectHeight * 2;
    font->image = f_171C_2190(size, "FONTIMAGE");
    font->locTable = (int far *)f_171C_2190(count * 2, "locTable");
    font->owTable = (int far *)f_171C_2190(count * 2, "owTable");
    fread(font->image, size, 1, fp);
    f_25E7_0008(font->locTable, count, fp);
    f_25E7_0008(font->owTable, count, fp);
    fclose(fp);
    font->proportional = (font->fontType & 0x2000) == 0;
    font->missing = font->lastChar - font->firstChar + 1;
    return font;
}

struct Font far * far font_DumpFont(struct Font far *font)
{
    if (font == 0)
        return 0;
    if (font->image)
        f_171C_2276(font->image);
    if (font->locTable)
        f_171C_2276(font->locTable);
    if (font->owTable)
        f_171C_2276(font->owTable);
    if (font)
        f_171C_2276(font);
    return 0;
}

extern unsigned far _fstrlen(char far *s);

struct Bitmap {
    int width;
    int height;
    char far *bits;
};

extern struct Bitmap far fd_50F6_392C;
extern void far f_2650_0107(char far *buf, int size);
extern int far fd_55B3_6770;
extern int far fd_55B3_6772;
extern void far f_2650_000F(char far *, char far *, int, int, int, int);

int far _font_StringWidth(unsigned char far *s, struct Font far *font)
{
    char c;
    int extra;
    int i;
    int result;

    i = 0;
    result = 0;
    if (font->proportional) {
        if (font->kernMax < 0)
            extra = 1;
        else
            extra = 0;
        while (s[i]) {
            if (font->owTable[s[i]] != -1) {
                result += (unsigned char)font->owTable[s[i]];
                i++;
            } else {
                result += (unsigned char)font->owTable[font->missing];
                i++;
            }
            result += extra;
        }
    } else {
        result = _fstrlen(s) * font->widMax;
    }
    return result;
}

int far _font_CharWidth(int ch, struct Font far *font)
{
    int extra;
    int i;
    int result;

    i = 0;
    result = 0;
    ch &= 0xff;
    if (font->proportional) {
        if (font->kernMax < 0)
            extra = 1;
        else
            extra = 0;
        if (font->owTable[ch] != -1)
            result += (unsigned char)font->owTable[ch];
        else
            result += (unsigned char)font->owTable[font->missing];
        result += extra;
    } else {
        result = font->widMax;
    }
    return result;
}

int far _font_FontHeight(struct Font far *font)
{
    return font->fRectHeight - 1;
}

int far _font_LineHeight(struct Font far *font)
{
    return font->leading + font->fRectHeight - 1;
}

struct Bitmap far * far font_MakeImage(unsigned char far *s, int x, struct Font far *font)
{
    register int i;
    int xofs;
    int width;
    int edge;
    int pen;
    int glyphWidth;
    int kk;
    unsigned char ch;
    int sx;

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
            ch = (unsigned char)font->missing;
        kk = (unsigned)font->owTable[ch] >> 8;
        if (font->proportional)
            width = (unsigned char)font->owTable[ch];
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
