#include <stdio.h>

static int greet(const char *name) {
    return printf("Hello, %s!\n", name);
}

int main(void) {
    greet("Virgo");
    return 0;
}
