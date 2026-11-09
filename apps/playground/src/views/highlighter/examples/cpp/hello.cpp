#include <iostream>
#include <string_view>
#include <vector>

void greet(std::string_view name) {
    std::cout << "Hello, " << name << "!\n";
}

int main() {
    const std::vector<std::string_view> names{"Ada", "Linus"};
    for (auto name : names) greet(name);
    return 0;
}
