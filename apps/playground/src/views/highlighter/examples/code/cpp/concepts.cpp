#include <concepts>

template<class T>
concept Addable = requires(T left, T right) {
    { left + right } -> std::same_as<T>;
};

template<Addable T>
constexpr T add(T left, T right) {
    return left + right;
}

static_assert(add(20, 22) == 42);
