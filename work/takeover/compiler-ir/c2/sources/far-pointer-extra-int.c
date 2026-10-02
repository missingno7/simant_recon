extern void far barrier(void far *p);
int far *keep_ptr(int far *input) { int hold; int far *saved; saved = input; hold = 0; barrier((void far *)&hold); if (hold == -1) return 0; return saved; }
