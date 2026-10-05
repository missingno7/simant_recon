
typedef char far * far *Handle;
extern char far * far fd_50F6_46D2;
extern int far puts(char far *);
char far fixturePixelsA[128] = { 11, 22, 33 };
char far fixturePixelsB[128] = { 44, 55, 66 };
struct FixtureCell { char far *cell; char spare[124]; };
struct FixtureCell far fixtureCell = {fixturePixelsA};
#define fixtureMaster fixtureCell.cell
char far * far fixtureMaster2 = fixturePixelsB;
char far * far derive(int n)
{
    return fd_50F6_46D2 + (n << 5);
}
int main(void)
{
    unsigned char far *bytes;
    unsigned far *words;
    int i;
    unsigned long cell;
    bytes=(unsigned char far *)&fd_50F6_46D2;
    if(sizeof(fd_50F6_46D2)!=4 || sizeof(Handle)!=4 || sizeof(char far *)!=4) {
        puts("FAIL_HANDLE_WIDTH"); return 1;
    }
    for(i=0;i<4;i++) if(bytes[i]) { puts("FAIL_INITIAL_ZERO"); return 2; }
    if(fd_50F6_46D2!=0) { puts("FAIL_NULL_REPRESENTATION"); return 3; }
    puts("PASS_INITIAL_ZERO_4BYTE_VIEW");
    fd_50F6_46D2=(char far *)&fixtureCell;
    if((Handle)fd_50F6_46D2!=&fixtureMaster) { puts("FAIL_TYPED_STORE"); return 4; }
    if(derive(1)!=fixturePixelsA+32 || derive(2)!=fixturePixelsA+64) {
        puts("FAIL_POINTER_CHAIN_OR_BYTE_STRIDE"); return 5;
    }
    fixtureMaster=fixturePixelsB;
    if(derive(1)!=fixturePixelsB+32) { puts("FAIL_CELL_REPOINT"); return 6; }
    puts("PASS_HANDLE_CELL_REPOINT_BYTE_STRIDE");
    words=(unsigned far *)&fd_50F6_46D2;
    cell=(unsigned long)&fixtureMaster2;
    if(words[0]!=(unsigned)(unsigned long)&fixtureMaster ||
       words[1]!=(unsigned)((unsigned long)&fixtureMaster>>16)) {
        puts("FAIL_RAW_OFFSET_SEGMENT_ORDER"); return 7;
    }
    words[0]=(unsigned)cell; words[1]=(unsigned)(cell>>16);
    if((Handle)fd_50F6_46D2!=&fixtureMaster2 || derive(3)!=fixturePixelsB+96) {
        puts("FAIL_RAW_WORD_ROUNDTRIP"); return 8;
    }
    fixtureMaster2=fixturePixelsA;
    if(derive(3)!=fixturePixelsA+96) { puts("FAIL_SECOND_CELL_REPOINT"); return 9; }
    for(i=0;i<4;i++) bytes[i]=0;
    if(fd_50F6_46D2!=0) { puts("FAIL_RAW_ZERO_RESET"); return 10; }
    puts("PASS_TYPED_RAW_WRITE_ZERO_RESET");
    return 0;
}
