#include <stdint.h>
#include <stdatomic.h>

_Static_assert(sizeof(uint32_t) == 4, "32-bit counter required");
static _Atomic uint32_t counter = 0;

typedef struct Result {
    uint32_t previous;
    uint32_t current;
} Result;

Result increment(uint32_t amount) {
    uint32_t previous = atomic_fetch_add(&counter, amount);
    return (Result){ .previous = previous, .current = previous + amount };
}
