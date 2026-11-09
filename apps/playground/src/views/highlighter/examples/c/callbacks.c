typedef int (*Predicate)(int value, void *context);

unsigned count_matches(const int *values, unsigned length,
                       Predicate predicate, void *context) {
    unsigned count = 0;
    for (unsigned i = 0; i < length; ++i) {
        if (predicate(values[i], context)) {
            ++count;
        }
    }
    return count;
}
