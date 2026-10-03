/* Data-only translation unit (hypothesis): the theme song descriptor, DGROUP _DATA 0064-00B7.
   Code-less: no code module references this data through its own _DATA segment.
   * fd_55B3_0064 points at the version stamp (external symbol: S27 relocation #365 is a target
     group of its own, so the string is another file's).
   * fd_55B3_00B4 points at the song record of this file (S27 relocation #1049, _DATA segment
     target; inside the program's _DATA group it follows the entries of the 00B8-1811 object,
     i.e. this object precedes that one in link order, so they are two files).
   The record has the layout of struct Song in modules 0000 and 284A (program[14], bank[14],
   Handle); 284A loads the song resource named by the record's number and copies its
   program/bank maps; the file name after it is not referenced by code. */

typedef char far * far *Handle;

struct Song {
    int program[14];
    unsigned bank[14];
    Handle data;
};

extern char g_0042[];

char *fd_55B3_0064 = g_0042;

static struct Song g_0068 = {
    { 0, 7, 7, 7, 7, 5, 5, 5, 5, 5, 5, 5, 5, 5 },
    { 0, 25, 53, 3, 54, 35, 46, 50, 51, 48, 0, 12, 43, 52 },
    0
};

static char g_00A4[16] = "antthme1.mid";

struct Song *fd_55B3_00B4 = &g_0068;
