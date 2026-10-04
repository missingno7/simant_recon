union VoicePayload {
    long offset;
    char far *sample;
};

struct Voice {
    int kind;
    union VoicePayload payload;
};

struct Chan {
    char type;
    char num;
    char c2;
    char c3;
    char c4;
    char c5;
};

struct Voice far fd_50F6_0000[56];
struct Chan far fd_50F6_4A4E[33];
