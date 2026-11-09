#ifndef SAMPLE_LOG_H
#define SAMPLE_LOG_H

#include <stdio.h>
#define CLAMP(x, low, high) \
    ((x) < (low) ? (low) : ((x) > (high) ? (high) : (x)))
#define LOG(fmt, ...) fprintf(stderr, fmt, __VA_ARGS__)

static inline int bounded(int value) {
    return CLAMP(value, 0, 100);
}

#endif
