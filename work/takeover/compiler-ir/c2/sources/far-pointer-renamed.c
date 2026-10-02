extern void far barrier(void);
int far *keep_ptr(int far *input) { int far *payload; payload = input; barrier(); return payload; }
