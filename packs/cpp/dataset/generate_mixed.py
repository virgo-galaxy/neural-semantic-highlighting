"""Original multiline C++ string/library tasks, outside visible probes."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
from .generate_curriculum import WORDS
PROGRAMS={
'raw-json':'''#include <string>
namespace {ns} {{
std::string {fn}(int {arg}) {{
    const auto payload = R"json({{
        "kind": "{word}",
        "enabled": true,
        "message": "Quoted text stays inside the raw string."
    }})json";
    return std::string(payload) + std::to_string({arg});
}}
}}
''',
'raw-delimiters':'''#include <string_view>
namespace {ns} {{
constexpr std::string_view {arg} = R"marker(
    A {word} note contains "quotes" and )" without ending.
    Backslashes \\ and syntax: return; class; std::vector<int>.
    These lines remain original text.
)marker";
int {fn}() {{ return {arg}.size() + {n}; }}
}}
''',
'raw-shader':'''#include <string_view>
constexpr std::string_view {arg} = R"glsl(
    #version 300 es
    precision highp float;
    out vec4 {word};
    void main() {{
        {word} = vec4(1.0, 0.5, 0.25, 1.0);
    }}
)glsl";
unsigned {fn}() {{ return {arg}.size() + {n}; }}
''',
'stream-output':'''#include <iostream>
#include <string>
namespace {ns} {{
void {fn}(const std::string& {arg}, int count) {{
    std::cout << "{word} result: " << {arg}
              << " has " << count << " entries\\n";
}}
}}
''',
'stream-loop':'''#include <iostream>
#include <vector>
#include <string_view>
int {fn}() {{
    std::vector<std::string_view> {arg}{{ "{word} first", "second item" }};
    for (const auto& value : {arg}) {{
        std::cout << "item: " << value << '\\n';
    }}
    return {n};
}}
''',
'stream-builder':'''#include <sstream>
#include <string>
std::string {fn}(const std::string& {arg}, unsigned count) {{
    std::ostringstream output;
    output << "{word}: " << count << " / " << {arg};
    return output.str();
}}
''',
'owning-entries':'''#include <memory>
#include <utility>
struct {item} {{
    int count;
    std::unique_ptr<{item}> tail;
}};
std::unique_ptr<{item}> {fn}(int {arg}) {{
    auto entry = std::make_unique<{item}>();
    entry->count = {arg};
    entry->tail = nullptr;
    return entry;
}}
''',
'attributes-fields':'''class {cls} {{
    int count_ = {n};
public:
    [[nodiscard]] int {fn}() const noexcept {{ return count_; }}
    [[nodiscard]] bool ready() const noexcept {{ return count_ > 0; }}
    void update(int {arg}) {{ count_ += {arg}; }}
}};
''',
'bindings-pairs':'''#include <utility>
namespace {ns} {{
int {fn}(int {arg}) {{
    auto [first, second] = std::pair{{ {arg}, {n} }};
    auto [low, high] = std::pair{{ first - 1, second + 1 }};
    return first + second + low + high;
}}
}}
''',
'constrained-operation':'''#include <concepts>
template<class T>
concept {cls} = requires(T left, T right) {{
    {{ left - right }} -> std::same_as<T>;
}};
template<{cls} T>
constexpr T {fn}(T {arg}, T other) {{
    return {arg} - other;
}}
''',
'unicode-comments':'''// 原始 {word} 数据和注释 🌙
#include <string_view>
namespace {ns} {{
// 保留换行、空格与引号 🌿
std::string_view {fn}(int {arg}) {{
    return {arg} > {n} ? "你好 星空 🌌 {word}" : "";
}}
}}
''',
'optional-template':'''#include <optional>
namespace {ns} {{
template<class T>
class {cls} {{
    std::optional<T> data_;
public:
    void assign(T {arg}) {{ data_ = {arg}; }}
    const T& {fn}() const {{ return data_.value(); }}
    bool ready() const {{ return data_.has_value(); }}
}};
}}
''',
}
def main():
 root=PackSpec.open('cpp').dataset_root/'sources/mixed-v1';hashes={}
 for index,(family,template) in enumerate(PROGRAMS.items()):
  for variant in range(24):
   rng=random.Random(62839+107*index+variant);w=rng.sample(WORDS,6);source=template.format(fn=w[0]+'_render',arg=w[1],word=w[2],item=w[3].title()+'Item',cls=w[4].title()+'Buffer',ns=w[5],n=rng.randrange(2,30));source=source.replace('    ',['    ','  ','\t'][variant%3])
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();target=root/family/f'{variant:02d}.cpp';target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve mixed source; use a new revision')
   if not target.exists():target.write_bytes(raw)
   hashes[target.relative_to(root).as_posix()]=hashlib.sha256(raw).hexdigest()
 license=root/'LICENSE'
 if not license.exists():license.write_text('Original multiline C++ syntax tasks for Neural Semantic Highlighting.\nPrivate development dataset; no Golden, Playground or upstream source copied.\n')
 lock={'format':'nsh-cpp-mixed-v1','generatorSha256':file_hash(Path(__file__)),'files':hashes};p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve existing mixed lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(hashes),'C++ mixed tasks across',len(PROGRAMS),'families')
if __name__=='__main__':main()
