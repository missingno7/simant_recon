extern volatile int probe_data_only;
void main(void) { if (probe_data_only == 0x1234) return; }
