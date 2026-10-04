unsigned char near probe[2] = {0x31,0x57};
int main(void) { return probe[0] + probe[1]; }
