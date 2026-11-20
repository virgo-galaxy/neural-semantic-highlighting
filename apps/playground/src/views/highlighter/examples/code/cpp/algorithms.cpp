#include <algorithm>
#include <vector>

std::vector<int> positive_squares(std::vector<int> values) {
    std::erase_if(values, [](int value) { return value <= 0; });
    std::transform(values.begin(), values.end(), values.begin(),
                   [](int value) { return value * value; });
    std::sort(values.begin(), values.end());
    return values;
}
