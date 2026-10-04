volatile int probe_cd_data = 0x5678;
int probe_cd_fn(void) { return probe_cd_data; }
