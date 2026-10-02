extern void far barrier(void);
long keep_long(long input) { long saved; saved = input; barrier(); return saved; }
