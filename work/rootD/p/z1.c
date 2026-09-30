extern int far k(void);
extern void far h(int a);
void far f(void)
{
    int c;
    for (;;) {
        c = k();
        switch (c) {
        case 1:
        case 13:
            goto done;
        }
        if (k())
            break;
    }
done:
    h(1);
    h(2);
}
