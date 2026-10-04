
struct Rect { int left,top,right,bottom; };
extern void (far * far win_drawHooks[])(int phase);
extern struct Rect far win_offsets[];
extern void far * far _fmemset(void far *, int, unsigned);
extern void far * far _fmemcpy(void far *, void far *, unsigned);
extern int far puts(char far *);
int calls;
void far callback(int phase) { calls += phase; }
int _fastcall windowIndex(int win) { return win >> 8; }
int _fastcall charWindowIndex(int win) { return (char)(win >> 8); }
void _fastcall setHook(int win, void (far *hook)(int phase))
{
    win_drawHooks[win >> 8] = hook;
}
int main(void)
{
    int i;
    unsigned char far *p;
    struct Rect input[40];
    struct Rect sentinel;
    p=(unsigned char far *)win_drawHooks;
    for(i=0;i<180;i++) if(p[i]) { puts("FAIL_INITIAL_FAR_HOOKS"); return 1; }
    p=(unsigned char far *)win_offsets;
    for(i=0;i<360;i++) if(p[i]) { puts("FAIL_INITIAL_FAR_RECTS"); return 2; }
    if(windowIndex(0x0000)!=0 || windowIndex(0x2800)!=40 ||
       windowIndex(0x2c00)!=44 || windowIndex(0x2d00)!=45 ||
       windowIndex((int)0x8000)!=-128 || windowIndex((int)0xff00)!=-1 ||
       charWindowIndex(0x2c00)!=44 || charWindowIndex(0x2d00)!=45 ||
       charWindowIndex((int)0x8000)!=-128 || charWindowIndex((int)0xff00)!=-1) {
        puts("FAIL_SIGNED_WINDOW_INDEX"); return 7;
    }
    sentinel.left=sentinel.top=sentinel.right=sentinel.bottom=(int)0x8000;
    _fmemset(win_drawHooks,0,180);
    for(i=0;i<45;i++) win_offsets[i]=sentinel;
    for(i=0;i<40;i++) {
        input[i].left=-100-i; input[i].top=200+i;
        input[i].right=-300-i; input[i].bottom=400+i;
    }
    _fmemcpy(win_offsets,input,320);
    for(i=0;i<40;i++)
        if(win_offsets[i].left!=-100-i || win_offsets[i].top!=200+i ||
           win_offsets[i].right!=-300-i || win_offsets[i].bottom!=400+i) {
            puts("FAIL_40_RECT_COPY"); return 3;
        }
    for(i=40;i<45;i++)
        if(win_offsets[i].left!=(int)0x8000 || win_offsets[i].top!=(int)0x8000 ||
           win_offsets[i].right!=(int)0x8000 || win_offsets[i].bottom!=(int)0x8000) {
            puts("FAIL_SENTINEL_TAIL"); return 4;
        }
    win_offsets[windowIndex(0x2c00)].right=-77;
    if(win_offsets[44].right!=-77 || win_offsets[43].right!=(int)0x8000) {
        puts("FAIL_SHIFTED_RECT_WRITE"); return 8;
    }
    setHook(0x0000,callback); setHook(0x2c00,callback);
    (*win_drawHooks[0])(1); (*win_drawHooks[44])(2);
    if(calls!=3) { puts("FAIL_CALLBACK"); return 5; }
    _fmemset(win_drawHooks,0,180);
    p=(unsigned char far *)win_drawHooks;
    for(i=0;i<180;i++) if(p[i]) { puts("FAIL_HOOK_CLEAR"); return 6; }
    puts("PASS_SIGNED_WINDOW_INDEX");
    puts("PASS_45_VIEW_RESET_40_COPY_CALLBACK"); return 0;
}
