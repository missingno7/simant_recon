typedef char far * far *Handle;
int far plain(Handle h) { int n; n=(*h)[1] << 3; return n; }
int far uns(Handle h) { int n; n=((unsigned char far *)*h)[1] << 3; return n; }
int far sig(Handle h) { int n; n=((signed char far *)*h)[1] << 3; return n; }
