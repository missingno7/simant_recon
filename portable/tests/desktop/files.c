#include "portable/whole_program/platform/desktop_files.h"
#include <stdio.h>
int main(int argc,char **argv)
{
    char root[2048],error[3072];
    if(argc!=4) return 64;
    int ok=simant_desktop_files(argv[1],argv[2][0]=='1',argv[3],root,sizeof(root),error,sizeof(error));
    puts(ok?root:error);return ok?0:70;
}
