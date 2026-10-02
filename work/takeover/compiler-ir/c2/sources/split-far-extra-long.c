extern char far * far fetch_text(void);
extern void far barrier(void);
int far use_text(void) { volatile long hold; char far *text; hold = 0L; text = fetch_text(); barrier(); return *text + (int)hold; }
