#pragma once
#include <optional>
#include <utility>

namespace demo {
template<class T>
class Slot {
    std::optional<T> value_;
public:
    void set(T value) { value_ = std::move(value); }
    const T& get() const { return value_.value(); }
    bool empty() const noexcept { return !value_.has_value(); }
};
}
