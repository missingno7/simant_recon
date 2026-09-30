/* Overlay section S23, code frame 39C7: info window and card display. */

int g_2E04[16] = { 0 };
int g_2E24 = 0;
int g_2E26 = 0x80;

void far XFlipLong(unsigned far *words)
{
    unsigned first = words[0];
    words[0] = words[1];
    words[1] = first;
}

void far FlipWords(unsigned char far *bytes, long length)
{
    long i;
    unsigned char saved;

    for (i = 0L; i < length; i += 2L) {
        saved = bytes[i];
        bytes[i] = bytes[i + 1L];
        bytes[i + 1L] = saved;
    }
}

void far DisplayCard(int card);

void far win_DrawInfoWindow(int flags)
{
    if (flags & 2)
        DisplayCard(g_2E26);
}

/* SCAFFOLD BEGIN: unrecovered same-module callees */
void far DisplayCard(int card)
{
}
/* SCAFFOLD END */
