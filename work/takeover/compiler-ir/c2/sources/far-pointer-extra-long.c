extern void far barrier(void far *p);
int far *keep_ptr(int far *input) { long hold; int far *saved; saved = input; hold = 0; barrier((void far *)&hold); if (hold == -1L) return 0; return saved; }
