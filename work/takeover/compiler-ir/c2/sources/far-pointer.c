extern void far barrier(void);
int far *keep_ptr(int far *input) { int far *saved; saved = input; barrier(); return saved; }
