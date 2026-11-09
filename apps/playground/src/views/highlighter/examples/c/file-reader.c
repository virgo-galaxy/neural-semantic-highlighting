#include <stdio.h>

long count_bytes(const char *path) {
    FILE *file = fopen(path, "rb");
    if (!file) return -1;

    long count = 0;
    while (fgetc(file) != EOF) {
        ++count;
    }
    fclose(file);
    return count;
}
