struct Event {
    int what;
    int message;
    int x4;
    int modifiers;
    int h;
    int v;
    int code;
    int xE;
};
struct EventBases {
    void far *current;
    void far *previous;
};
extern struct Event far fd_50F6_49FA;
extern struct Event far fd_50F6_4A0A;
struct EventBases far eventBases = {
    (void far *)&fd_50F6_49FA,
    (void far *)&fd_50F6_4A0A
};
