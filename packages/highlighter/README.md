# @nsh/highlighter

Neural code highlighting directly in the browser. Currently private and
unpublished; see the repository README for local tarball installation.

```ts
import { createHighlighter } from "@nsh/highlighter";
import "@nsh/highlighter/theme.css";

const highlighter = createHighlighter(); // Reuse this instance.
const { html } = await highlighter.highlight(source, { language: "tsx" });
container.innerHTML = html;
```

`html` is an escaped complete `<pre class="nsh"><code>` block; `value` is the token
markup alone. `highlightElement(codeElement)` reads `language-*` or `data-language`.
Use explicit languages; there is no automatic detection. Inference is asynchronous
and runs in a Web Worker. The consumer needs no Python process or server endpoint.
Call `close()` to terminate the worker when finished. Inference is client-only;
importing the module itself does not start a worker.

To select deployment assets:

```ts
import { createHighlighter } from "@nsh/highlighter/core";
import typescript from "@nsh/highlighter/languages/typescript";
const highlighter = createHighlighter({ languages: [typescript] });
```

JS/TS includes JSX/TSX. CSS includes SCSS/Less. HTML, Vue and Svelte descriptors
include their JS/TS/CSS dependencies automatically; PHP includes HTML and its
child dependencies. Default registration covers 28 packs, including Swift,
Kotlin, R, Scala, Ruby and Lua. Flutter shares Dart's model. Weights are fetched
lazily. Models are about 3.7 MB each, with a shared 14.8 MB uncompressed WASM asset. Vite production bundling is verified; other bundlers are
not yet verified. HTTPS or localhost and a modern WASM/Worker browser are required.

`theme.css` provides the Default preset. For all presets:

```ts
import "@nsh/highlighter/themes.css";
import { themes } from "@nsh/highlighter/themes";
```

Set `data-nsh-preset="default"`, `"muted"` or `"contrast"` on a code block or its
ancestor. Independently set `data-nsh-theme="light"` / `"dark"` on an ancestor,
or `data-theme` on an individual `.nsh` block. Missing a preset selects Default.
For a single preset, import `@nsh/highlighter/themes/muted.css` and set its ID.
The catalog contains IDs/names/descriptions; it does not load CSS by itself.

Every preset has complete paired palettes plus optional language accents.
Switching styles or mode reuses the existing highlighted markup. Public
`--nsh-*` variables override both base and language colors; font/layout rules
can be customized with ordinary application CSS.
Models retain their measured limitations; this package does not claim perfect
classification or full highlight.js API compatibility.

Java source is available with `{ language: "java" }`, including package/module
descriptors. To ship only Java, import the descriptor from
`@nsh/highlighter/languages/java` and pass it to the configurable `./core` entry.
All three built-in theme presets cover its roles. No JDK is required by consumers.

C# source uses `{ language: "csharp" }`, with `cs` and `c#` aliases. Import
`@nsh/highlighter/languages/csharp` with the configurable `./core` entry to include
only that model. Browser consumers need no .NET SDK, Mono or source parser.

C source uses `{ language: "c" }`, or the selective descriptor
`@nsh/highlighter/languages/c`. C++ uses `{ language: "cpp" }`, with `c++` and
`cxx` aliases, or `@nsh/highlighter/languages/cpp`. They are separate models;
existing `.h` extension mapping remains C. Pass `cpp` explicitly for C++ header
contents. Consumers need no C/C++ compiler, SDK, parser or preprocessor.

PHP uses `{ language: "php" }`, including tagged source, tagless snippets and
`.phtml` templates. Selective `@nsh/highlighter/languages/php` registers existing
HTML/JS/CSS dependencies for predicted-region composition. The selective Vite
build emits four model assets, fetched lazily when needed. No PHP interpreter,
SDK, Composer or Python/server provider is required. Base PHP/region accuracy
and visible composed template accuracy are separate in the repository report.

Svelte uses `{ language: "svelte" }` for `.svelte` source. Selective
`@nsh/highlighter/languages/svelte` registers existing JS/TS and CSS/SCSS/Less
dependencies; a Vite build emits three model assets, fetched on demand. Legacy
component syntax and common Svelte 5 runes/snippets share this entry. Consumers
need no Svelte SDK/runtime, preprocessor or Python/server provider. Whole attribute
values are opaque; template expressions and script/style bodies use only predicted
regions. See [Svelte evidence](../../packs/svelte/model/BENCHMARKS.md) and
[known issues](../../packs/svelte/model/KNOWN_ISSUES.md) before treating base or
visible composed scores as general accuracy.

Rust uses `{ language: "rust" }` (or `"rs"`) for original `.rs` source.
Selective `@nsh/highlighter/languages/rust` emits one model asset and requires no
Rust compiler, Cargo, Python provider or language parser. Common stable
2018/2021/2024 syntax shares one entry; compiler compatibility is not inferred.
See [Rust evaluation](../../packs/rust/model/BENCHMARKS.md) and
[known issues](../../packs/rust/model/KNOWN_ISSUES.md), including raw/format-string
boundaries, macro DSLs and source-local role approximations.

Zig uses `{ language: "zig" }` for original `.zig` source, targeting **0.17.1 only**.
Selective `@nsh/highlighter/languages/zig` emits one model asset; no Zig compiler,
SDK, Python provider or parser is needed by the frontend. Historical releases,
master and ZON are outside this pack. See [Zig evaluation](../../packs/zig/model/BENCHMARKS.md)
and [known issues](../../packs/zig/model/KNOWN_ISSUES.md).

Dart uses `{ language: "dart" }` for original `.dart` source, including common
Flutter widget code. Selective `@nsh/highlighter/languages/dart` emits one model
asset. Consumers require no Dart/Flutter SDK, analyzer, language parser or Python
provider. See [Dart evaluation](../../packs/dart/model/BENCHMARKS.md) and
[known issues](../../packs/dart/model/KNOWN_ISSUES.md), including literal boundaries
and approximate local/constructor roles.

Flutter supports `{ language: "flutter" }` and
`@nsh/highlighter/languages/flutter`. The descriptor re-exports Dart; importing
both emits one Dart model asset. Return values and HTML normalize to canonical
`dart`, so Dart theme/CSS overrides apply. `highlightElement` accepts
`language-flutter`, and `highlightTokens` accepts the same alias. The Playground
has a separate Flutter entry; files remain `.dart`. See
[Flutter coverage and limits](../../packs/dart/model/FLUTTER.md).

Swift uses `{ language: "swift" }` for `.swift` source, including common SwiftUI
views, bindings, result builders and actor/async syntax. Selective
`@nsh/highlighter/languages/swift` emits one model asset; no Swift SDK, Xcode,
parser or Python process is required in a frontend application. See
[Swift evaluation](../../packs/swift/model/BENCHMARKS.md) and
[known issues](../../packs/swift/model/KNOWN_ISSUES.md).

Kotlin uses `{ language: "kotlin" }` for `.kt`/`.kts`, including common coroutine,
Compose and Gradle Kotlin-script syntax. `kt`, `kts`, `kotlin-script` and
case-normalized IDs share one descriptor and canonical `kotlin` output.
Selective `@nsh/highlighter/languages/kotlin` emits one model asset. No JDK,
Kotlin SDK, Gradle, Android SDK, parser or Python process is required in frontend
applications. Existing themes and custom CSS apply. See [evaluation](../../packs/kotlin/model/BENCHMARKS.md)
and [known limits](../../packs/kotlin/model/KNOWN_ISSUES.md).

R uses `{ language: "r" }`. Original .R/.r/.Rprofile source; common statistical/data, native and magrittr pipe syntax.
Selective `@nsh/highlighter/languages/r` emits one model asset and requires no
language SDK, parser or Python process. Existing themes/custom CSS apply. See
[evaluation](../../packs/r/model/BENCHMARKS.md) and [known limits](../../packs/r/model/KNOWN_ISSUES.md).

Scala uses `{ language: "scala" }`. Common Scala 2/3 .scala/.sc/.sbt source, significant indentation, givens/using, extensions, enums, generics and interpolated strings.
Selective `@nsh/highlighter/languages/scala` emits one model asset and requires no
language SDK, parser or Python process. Existing themes/custom CSS apply. See
[evaluation](../../packs/scala/model/BENCHMARKS.md) and [known limits](../../packs/scala/model/KNOWN_ISSUES.md).

Ruby uses `{ language: "ruby" }`. Aliases `rb`, `rake`, `gemspec`, `gemfile` and `rakefile` normalize to `ruby`. Common modern Ruby .rb/.rake/.gemspec and Gemfile/Rakefile syntax, classes/modules, blocks, patterns, Rails-style calls, heredocs and percent/regex literals.
Selective `@nsh/highlighter/languages/ruby` emits one model asset and requires no
language SDK, parser or Python process. Existing themes/custom CSS apply. See
[evaluation](../../packs/ruby/model/BENCHMARKS.md) and [known limits](../../packs/ruby/model/KNOWN_ISSUES.md).

Lua uses `{ language: "lua" }`. Common Lua 5.x .lua functions, closures, tables, methods, long strings/comments, 5.4 attributes and 5.5 global declarations/named varargs.
Selective `@nsh/highlighter/languages/lua` emits one model asset and requires no
language SDK, parser or Python process. Existing themes/custom CSS apply. See
[evaluation](../../packs/lua/model/BENCHMARKS.md) and [known limits](../../packs/lua/model/KNOWN_ISSUES.md).
