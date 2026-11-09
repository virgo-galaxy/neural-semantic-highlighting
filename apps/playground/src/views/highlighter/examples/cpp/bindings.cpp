#include <map>
#include <string>
#include <utility>

int total_scores(const std::map<std::string, int>& scores) {
    int total = 0;
    for (const auto& [name, score] : scores) {
        total += score;
    }
    return total;
}

auto coordinates() {
    auto [x, y] = std::pair{3.0, 4.0};
    return x * x + y * y;
}
