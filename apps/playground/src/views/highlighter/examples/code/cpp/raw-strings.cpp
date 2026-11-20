#include <string_view>

// 原始文本、引号和换行保持不变 🌙
constexpr std::string_view page = R"html(
<article class="card">
    <h1>Welcome 🌌</h1>
    <p>return, class and #define are text.</p>
</article>
)html";

constexpr auto limit = 1'024ULL;
constexpr auto scale = 0x1.fp+2;
