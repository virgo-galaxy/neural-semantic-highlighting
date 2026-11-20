#include <string>
#include <utility>

class Counter {
    std::string name_;
    int value_ = 0;
public:
    explicit Counter(std::string name) : name_(std::move(name)) {}
    void increment(int amount = 1) { value_ += amount; }
    [[nodiscard]] int value() const noexcept { return value_; }
    const std::string& name() const { return name_; }
};
