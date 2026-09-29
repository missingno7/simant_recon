/* Overlay section S09, code frame 36EE: text entry field helpers. */

extern char near g_3DDE;
extern char near g_3DDC;
extern void far f_1B4E_0110(int x, int y, int c);

char g_2970 = 0;

void far o09_36EE_0092(int x, int y, char far *text, int maxLen, int flags);

/* draws count blanks from (x, y) */
void far o09_36EE_000A(int x, int y, int count)
{
    while (count--) {
        f_1B4E_0110(x, y, ' ');
        x += g_3DDE;
    }
}

/* text-cell to pixel coordinates, then edit */
void far o09_36EE_003C(int col, int row, char far *text, int maxLen, int flags)
{
    o09_36EE_0092(col = (col >> 8) + g_3DDE * (col & 0xff),
                  row = g_3DDC * (row & 0xff) + (char)(row >> 8) * g_3DDC / 14,
                  text, maxLen, flags);
}

/* SCAFFOLD BEGIN: unrecovered same-module functions */
void far o09_36EE_0092(int x, int y, char far *text, int maxLen, int flags)
{
    char far *p = ":;,.=+-_\\/*";
}
/* SCAFFOLD END */
