extern char far * far fetch_text(void);
extern void far barrier(void);
int far use_text(void) { char far *text; text = fetch_text(); barrier(); return *text; }
