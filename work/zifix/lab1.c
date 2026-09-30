extern int far g(int);
int far f(int a)
{
    int r;
    r = g(a);
    if (r)
        goto skip;
    r = g(r + 1);
skip:
    r = g(r + 2);
    return r;
}
