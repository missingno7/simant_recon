int far IsItDirt(int value)
{
    if (value >= 0x20 && value <= 0x2e)
        return 1;
    return 0;
}
