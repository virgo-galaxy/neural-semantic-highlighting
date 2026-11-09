"""Original C++ tasks, grouped by complete families before windowing."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash

TEMPLATES={
'functions':'''#include <string>
namespace {ns} {{
int {fn}(int {arg}, int limit) {{
    int total = {arg} + {n};
    return total > limit ? total : limit;
}}
}}
''',
'class-methods':'''namespace {ns} {{
class {cls} {{
    int count_;
public:
    explicit {cls}(int {arg}) : count_({arg}) {{}}
    int {fn}(int delta) const {{ return count_ + delta; }}
}};
}}
''',
'class-property':'''#include <string>
class {cls} {{
    std::string name_;
public:
    explicit {cls}(std::string {arg}) : name_({arg}) {{}}
    const std::string& {fn}() const noexcept {{ return name_; }}
}};
''',
'constructor-destructor':'''class {cls} {{
    int* value_;
public:
    {cls}() : value_(new int({n})) {{}}
    ~{cls}() {{ delete value_; }}
    int {fn}() const {{ return *value_; }}
}};
''',
'out-of-class':'''namespace {ns} {{
class {cls} {{
    int value_;
public:
    explicit {cls}(int value);
    int {fn}() const;
}};
{cls}::{cls}(int value) : value_(value) {{}}
int {cls}::{fn}() const {{ return value_ + {n}; }}
}}
''',
'structs':'''struct {item} {{
    double width;
    double height;
}};
{item} {fn}(const {item}& {arg}, double factor) {{
    return {{ {arg}.width * factor, {arg}.height * factor }};
}}
''',
'inheritance':'''class {base} {{
public:
    virtual ~{base}() = default;
    virtual int {fn}() const = 0;
}};
class {cls} final : public {base} {{
public:
    int {fn}() const override {{ return {n}; }}
}};
''',
'copy-move':'''#include <string>
class {cls} {{
    std::string text_;
public:
    {cls}() = default;
    {cls}(const {cls}&) = delete;
    {cls}({cls}&&) noexcept = default;
    {cls}& operator=({cls}&&) noexcept = default;
    void {fn}(std::string text) {{ text_ = text; }}
}};
''',
'overloaded-operator':'''struct {item} {{
    int count;
    {item}& operator+=(int {arg}) {{ count += {arg}; return *this; }}
    bool operator==(const {item}& other) const {{ return count == other.count; }}
}};
''',
'conversion-operator':'''struct {item} {{
    int count;
    explicit operator bool() const {{ return count > {n}; }}
    int {fn}() const {{ return count; }}
}};
''',
'friend':'''class {cls} {{
    int value_ = {n};
    friend int {fn}(const {cls}&);
}};
int {fn}(const {cls}& {arg}) {{ return {arg}.value_; }}
''',
'enum-scoped':'''namespace {ns} {{
enum class {state} : unsigned {{ pending, ready = {n}, done }};
bool {fn}({state} {arg}) {{ return {arg} == {state}::ready; }}
}}
''',
'enum-flags':'''enum {state} {{ {upper}_NONE=0, {upper}_READ=1, {upper}_WRITE=2 }};
unsigned {fn}({state} {arg}) {{
    return static_cast<unsigned>({arg}) | {upper}_WRITE;
}}
''',
'namespace-alias':'''namespace {ns} {{ namespace detail {{ int {fn}(int n) {{ return n+{n}; }} }} }}
namespace {alias} = {ns}::detail;
int {other}(int {arg}) {{ return {alias}::{fn}({arg}); }}
''',
'using-alias':'''#include <map>
#include <string>
namespace {ns} {{
using {item} = std::map<std::string, int>;
int {fn}(const {item}& {arg}) {{ return static_cast<int>({arg}.size()); }}
}}
''',
'template-function':'''template<typename T>
T {fn}(const T& {arg}, const T& other) {{
    return {arg} < other ? other : {arg};
}}
''',
'template-class':'''namespace {ns} {{
template<class T>
class {cls} {{
    T value_;
public:
    explicit {cls}(T value) : value_(value) {{}}
    const T& {fn}() const {{ return value_; }}
}};
}}
''',
'template-array':'''#include <array>
template<class T, unsigned N>
T {fn}(const std::array<T, N>& {arg}) {{
    T sum{{}};
    for (const T& value : {arg}) {{ sum += value; }}
    return sum;
}}
''',
'variadic-template':'''template<class... Values>
auto {fn}(Values... {arg}) {{
    return ({arg} + ... + {n});
}}
''',
'alias-template':'''#include <vector>
namespace {ns} {{
template<typename T> using {item} = std::vector<T>;
{item}<int> {fn}(int {arg}) {{ return {{ {arg}, {n}, {n2} }}; }}
}}
''',
'specialization':'''template<class T> struct {item} {{ static int {fn}() {{ return {n}; }} }};
template<> struct {item}<bool> {{ static int {fn}() {{ return {n2}; }} }};
int {other}() {{ return {item}<bool>::{fn}(); }}
''',
'dependent-type':'''template<class Container>
typename Container::value_type {fn}(const Container& {arg}) {{
    typename Container::value_type total{{}};
    for (const auto& value : {arg}) {{ total += value; }}
    return total;
}}
''',
'constexpr':'''namespace {ns} {{
constexpr int {fn}(int {arg}) {{
    return {arg} <= 1 ? 1 : {arg} * {fn}({arg} - 1);
}}
static_assert({fn}(3) == 6, "{word} compile-time check");
}}
''',
'concept':'''template<class T>
concept {cls} = requires(T value) {{ value + 1; value * 2; }};
template<{cls} T>
T {fn}(T {arg}) {{ return {arg} + {n}; }}
''',
'requires':'''template<class T>
requires (sizeof(T) >= 2)
T {fn}(T {arg}) {{
    return {arg} * static_cast<T>({n});
}}
''',
'lambda-capture':'''#include <algorithm>
#include <vector>
int {fn}(std::vector<int> {arg}, int offset) {{
    auto transform = [offset](int value) {{ return value + offset; }};
    std::transform({arg}.begin(), {arg}.end(), {arg}.begin(), transform);
    return {arg}.front();
}}
''',
'lambda-init-capture':'''int {fn}(int {arg}) {{
    auto next = [count = {n}] (int delta) mutable {{ count += delta; return count; }};
    return next({arg});
}}
''',
'generic-lambda':'''#include <utility>
namespace {ns} {{
auto {fn}(int {arg}) {{
    auto twice = [](auto value) {{ return value + value; }};
    return twice({arg}) + twice({n}.0);
}}
}}
''',
'structured-binding':'''#include <utility>
namespace {ns} {{
int {fn}(int {arg}) {{
    auto [left, right] = std::pair{{ {arg}, {n} }};
    return left + right;
}}
}}
''',
'range-loop':'''#include <map>
#include <string>
int {fn}(const std::map<std::string, int>& {arg}) {{
    int total = {n};
    for (const auto& [key, value] : {arg}) {{ total += value; }}
    return total;
}}
''',
'if-init':'''#include <map>
int {fn}(const std::map<int, int>& {arg}, int key) {{
    if (auto iter = {arg}.find(key); iter != {arg}.end()) {{ return iter->second; }}
    return {n};
}}
''',
'unique-pointer':'''#include <memory>
struct {item} {{ int value; }};
int {fn}(int {arg}) {{
    auto entry = std::make_unique<{item}>({item}{{ {arg} }});
    return entry->value + {n};
}}
''',
'shared-pointer':'''#include <memory>
class {cls} {{ public: int value = {n}; }};
std::shared_ptr<{cls}> {fn}() {{
    auto entry = std::make_shared<{cls}>();
    return entry;
}}
''',
'optional':'''#include <optional>
#include <string>
std::optional<int> {fn}(const std::string& {arg}) {{
    if ({arg}.empty()) return std::nullopt;
    return static_cast<int>({arg}.size()) + {n};
}}
''',
'variant':'''#include <variant>
#include <string>
using {item} = std::variant<int, std::string>;
int {fn}(const {item}& {arg}) {{
    return std::visit([](const auto& value) {{ return static_cast<int>(sizeof(value)); }}, {arg});
}}
''',
'containers':'''#include <vector>
#include <string>
std::vector<std::string> {fn}(std::string {arg}) {{
    std::vector<std::string> result;
    result.emplace_back("{word} ready");
    result.push_back({arg});
    return result;
}}
''',
'algorithm':'''#include <algorithm>
#include <vector>
void {fn}(std::vector<int>& {arg}) {{
    std::sort({arg}.begin(), {arg}.end());
    auto end = std::unique({arg}.begin(), {arg}.end());
    {arg}.erase(end, {arg}.end());
}}
''',
'ranges':'''#include <ranges>
#include <vector>
int {fn}(const std::vector<int>& {arg}) {{
    int total = 0;
    for (int n : {arg} | std::views::filter([](int v) {{ return v > {n}; }})) {{ total += n; }}
    return total;
}}
''',
'span':'''#include <span>
int {fn}(std::span<const int> {arg}) {{
    int total = {n};
    for (int value : {arg}) {{ total += value; }}
    return total;
}}
''',
'exceptions':'''#include <stdexcept>
int {fn}(int {arg}) {{
    try {{
        if ({arg} < 0) throw std::runtime_error("{word} invalid value");
        return {arg} + {n};
    }} catch (const std::exception& error) {{ return -1; }}
}}
''',
'casts':'''struct {base} {{ virtual ~{base}() = default; }};
struct {cls} : {base} {{ int value = {n}; }};
int {fn}({base}* {arg}) {{
    if (auto* item = dynamic_cast<{cls}*>({arg})) return item->value;
    return -1;
}}
''',
'raw-string':'''#include <string>
namespace {ns} {{
std::string {fn}(int {arg}) {{
    const auto text = R"note(<section name="{word}">
        text with "quotes" and a backslash \\n
    </section>)note";
    return std::string(text) + std::to_string({arg});
}}
}}
''',
'format-string':'''#include <cstdio>
int {fn}(const char* {arg}, unsigned count) {{
    char buffer[256];
    return std::snprintf(buffer, sizeof(buffer), "{word} %s has %u entries\\n", {arg}, count);
}}
''',
'unicode':'''// 保留原始源码 🌙 {word}
#include <string>
std::string {fn}(int {arg}) {{
    const std::string title = "欢迎 🌌 {word}";
    return {arg} > {n} ? title : "";
}}
''',
'numbers':'''namespace {ns} {{
constexpr auto {arg} = 1'024ULL + {n}U;
double {fn}() {{ return 0x1.fp+2 + 1.25e-2 + {arg}; }}
}}
''',
'macros':'''#define {upper}_SCALE(x) \\
    ((x) * {n})
namespace {ns} {{
int {fn}(int {arg}) {{ return {upper}_SCALE({arg}); }}
}}
''',
'header-guards':'''#ifndef {upper}_DATA_HPP
#define {upper}_DATA_HPP
namespace {ns} {{
class {cls} {{ public: int {fn}(int value) const; }};
}}
#endif
''',
'variadic-macro':'''#include <cstdio>
#define {upper}_TRACE(fmt, ...) std::printf(fmt, __VA_ARGS__)
int {fn}(int {arg}) {{
    return {upper}_TRACE("{word}: %d\\n", {arg});
}}
''',
'attributes':'''namespace {ns} {{
class {cls} {{
    int value_ = {n};
public:
    [[nodiscard]] int {fn}() const noexcept {{ return value_; }}
}};
}}
''',
'function-pointer':'''namespace {ns} {{
using {item} = int (*)(int);
int {fn}({item} callback, int {arg}) {{
    return callback({arg}) + {n};
}}
}}
''',
'comments':'''/* {word} comment: template<class T> and return "text" */
namespace {ns} {{
int {fn}(int {arg}) {{
    // a declaration-looking comment stays opaque
    return {arg} + {n}; /* done */
}}
}}
''',
'initializer-list':'''#include <initializer_list>
class {cls} {{
    int total_ = 0;
public:
    {cls}(std::initializer_list<int> values) {{
        for (int value : values) total_ += value;
    }}
    int {fn}() const {{ return total_ + {n}; }}
}};
''',
}
WORDS='atlas cedar delta ember flora glade harbor ivory jade kernel lagoon maple nova orbit prism quartz river solar tundra umber violet willow xenon yellow zenith aurora breeze canyon dawn echo forest grove horizon iris juniper meadow north opal pine'.split()
def main():
 root=PackSpec.open('cpp').dataset_root/'sources/curriculum-v1';hashes={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   rng=random.Random(51749+103*index+variant);w=rng.sample(WORDS,10);values=dict(fn=w[0]+'_read',other=w[1]+'_apply',arg=w[2],cls=w[3].title()+'Store',item=w[4].title()+'Entry',base=w[5].title()+'Base',state=w[6].title()+'State',word=w[7],upper=w[7].upper(),ns=w[8],alias=w[9],n=rng.randrange(2,24),n2=rng.randrange(25,99))
   source=template.format(**values);source=source.replace('    ',['    ','  ','\t'][variant%3])
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();target=root/family/f'{variant:02d}.cpp';target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve original C++ tasks; use a new revision')
   if not target.exists():target.write_bytes(raw)
   hashes[target.relative_to(root).as_posix()]=hashlib.sha256(raw).hexdigest()
 license=root/'LICENSE'
 if not license.exists():license.write_text('Original C++ syntax tasks authored for Neural Semantic Highlighting.\nPrivate development dataset. No Golden, Playground or upstream source copied.\n')
 lock={'format':'nsh-cpp-curriculum-v1','generatorSha256':file_hash(Path(__file__)),'files':hashes};p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve existing curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(hashes),'C++ tasks across',len(TEMPLATES),'families')
if __name__=='__main__':main()
