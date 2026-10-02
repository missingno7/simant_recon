extern void far barrier(void);
int keep_word(int input) { int saved; saved = input; barrier(); return saved; }
