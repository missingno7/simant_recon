extern int g; extern int h; extern char far *rp; extern int far close(int); extern int far gg(int, int, char far *, int); extern int far open(char far *, int);
void far f1(int a) { g = a; }
int far f2(int a) { int n; n = a; g = n; return n; }
void far f3(void) { close(h); }
void far f4(int a) { if (a < 0) a = 0x7fff; g = a; }
int far f5(char far *p) { h = open(p, 0x8000); if (h <= 0) return 0; return 1; }
int far f6(int a, int b, int c, char far *p, int d) { return gg(b, c, p, d); }
int far f7(int far *p, int n) { register int i; register int far *q = p; int s = 0; for (i = 0; i < n; i++) s += q[i]; return s; }
