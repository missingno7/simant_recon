extern char far * far fetch_text(void);
extern void far barrier(void);
int far use_text(void) { volatile int hold; char far *text; hold = 0; text = fetch_text(); barrier(); return *text + hold; }
