struct SaveRec {
    int size;
    int count;
    void far *data;
};

extern int far fd_50F6_0468;
extern int far fd_50F6_0370;
extern int far fd_50F6_024E;

struct SaveRec far flagRecords[4] = {
    { 2, 1, (void far *)&fd_50F6_024E },
    { 2, 1, (void far *)&fd_50F6_0370 },
    { 2, 1, (void far *)&fd_50F6_0468 },
    { 0, 0, 0 }
};
