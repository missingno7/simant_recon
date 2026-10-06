#include <stdio.h>
#include <string.h>
#include <direct.h>

extern int far f_1F66_00AF(int drive, char far *path);

static void check(int depth)
{
    char path[256];
    int result;
    int length;
    memset(path, 0x55, sizeof(path));
    result = f_1F66_00AF(3, path);
    if (!result) {
        printf("depth=%d failed\n", depth);
        return;
    }
    length = strlen(path);
    printf("depth=%d length=%d nul=%d path=%s\n", depth, length, length, path);
    if (path[length-1] != '\\') {
        strcat(path, "\\");
        printf("after-slash=%d requires=%d fits67=%d\n", strlen(path), strlen(path)+1, strlen(path)+1<=67);
    }
}

int main(void)
{
    int n;
    chdir("C:\\");
    check(0);
    for (n=1; n<=7; n++) {
        if (chdir("AAAAAAAA")) return 1;
        check(n);
    }
    if (chdir("A")) return 2;
    check(8);
    return 0;
}
