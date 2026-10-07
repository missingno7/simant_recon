#include <stddef.h>
int open(const char *, int, ...);
int close(int);
int read(int, void *, unsigned);
int write(int, const void *, unsigned);
long lseek(int, long, int);
int access(const char *, int);
int remove(const char *);
