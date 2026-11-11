/*
 * Typed SOURCE_ONLY_DOS candidate for the five Ralloc DGROUP objects.
 * This translation unit owns only these five uninitialized objects. Their
 * definitions follow the independently pinned source and storage controls in
 * ../memory-state-probe.py. It makes no historical placement or TU-order claim.
 */
typedef struct Block {
    int handle;
    long size;
    unsigned paras;
    unsigned char type;
    unsigned char lock;
    long age;
    unsigned next;
    unsigned prev;
    unsigned char attr;
    char name[13];
} Block;

unsigned near g_91A0;
unsigned near g_91A2;
Block far * near g_91A4;
Block far * near g_91A8;
Block far * near g_91AC;
