# Model benchmarks

There are **40 model packs**, with browser inference and Playground examples.
Some source kinds share weights, including XML/SVG and JSON/JSONC; Flutter shares Dart.
The browser conversion preserves the selected weights without retraining or
quantization. The recorded [Diff/Patch browser verification](diff-browser-verification.json)
reported **410/410** exact browser/native comparisons and **180** passing frontend
tests. Independent local-package checks cover public imports, original source
text, themes and custom CSS. [Browser verification](browser-runtime.md)
keeps the earlier rollout results separately. These are runtime/packaging checks,
not a new accuracy evaluation.

All selected models use **512 UTF-8 bytes per inference window**. Longer documents
are processed in multiple windows; 512 bytes is not a file-size limit.

**Parameters** is the selected model's parameter count. **ONNX size** is its
uncompressed browser `.onnx` file size, with **1 MB = 1,000,000 bytes**. Each row
counts only that model, excluding the shared runtime, JS/CSS and any child-model
dependencies used for composed highlighting. See [model deployment](model-delivery.md)
for how to ship a subset of models.

The tables report **exact-span F1**: token start, end and semantic type must match.
It is not character accuracy or the percentage of perfect files. Different test
sets and sample sizes are not directly comparable. Reports retain known limits.

## Code languages

[Full support details and measured limits](code-languages.md).

| Name                                                           | Accepted content IDs / aliases                         | Model        | Parameters | ONNX size | Measured test exact-span F1                                                                                                         |
| -------------------------------------------------------------- | ------------------------------------------------------ | ------------ | ---------: | --------: | ----------------------------------------------------------------------------------------------------------------------------------- |
| [JavaScript / TypeScript](../packs/typescript/model/README.md) | `typescript`, `ts`, `javascript`, `js`, `jsx`, `tsx`   | `typescript` |    897,833 |  3.614 MB | [99.45%; real TSX 99.39%](../packs/typescript/model/BENCHMARKS.md) — exposed 50-file regression; first-read 24-file product cohort  |
| [Go](../packs/go/model/README.md)                              | `go`                                                   | `go`         |    894,614 |  3.601 MB | [99.03%](../packs/go/model/README.md#selected-candidate) — natural test                                                             |
| [CSS / SCSS / Less](../packs/css/model/README.md)              | `css`, `scss`, `less`                                  | `css`        |    894,227 |  3.599 MB | [CSS 99.04%; SCSS 99.40%; Less 99.42%](../packs/css/model/BENCHMARKS.md) — natural test, per language                               |
| [HTML](../packs/html/model/README.md)                          | `html`                                                 | `html`       |    893,711 |  3.597 MB | [Markup 96.37%; composed 96.53%](../packs/html/model/BENCHMARKS.md) — natural test, separate scopes                                 |
| [Vue](../packs/vue/model/README.md)                            | `vue`                                                  | `vue`        |    894,485 |  3.600 MB | [97.12%](../packs/vue/model/BENCHMARKS.md) — natural composed test; profile results are separate in the report                      |
| [Python](../packs/python/model/README.md)                      | `python`, `py`                                         | `python`     |    895,398 |  3.607 MB | [91.48%](../packs/python/model/BENCHMARKS.md) — exposed 4-file regression; additional 19 files 90.87% (separate cohort)             |
| [Shell](../packs/bash/model/README.md)                         | `bash`, `sh`, `shell`, `zsh`, `csh`, `tcsh`            | `bash`       |    894,366 |  3.602 MB | [87.12%](../packs/bash/model/BENCHMARKS.md) — exposed 11-file regression; Bash 94.29%; additional 12 files 90.91% (separate cohort) |
| [Perl](../packs/perl/model/README.md)                          | `perl`                                                 | `perl`       |    894,995 |  3.603 MB | [91.00%](../packs/perl/model/BENCHMARKS.md) — exposed 4-file regression; additional 16 files 88.33% (separate cohort)               |
| [AWK](../packs/awk/model/README.md)                            | `awk`                                                  | `awk`        |    893,582 |  3.596 MB | [96.89%](../packs/awk/model/BENCHMARKS.md) — natural test                                                                           |
| [SQL](../packs/sql/model/README.md)                            | `sql`                                                  | `sql`        |    894,737 |  3.602 MB | [90.08%](../packs/sql/model/BENCHMARKS.md) — exposed 7-file regression                                                              |
| [PowerShell](../packs/powershell/model/README.md)              | `powershell`, `pwsh`, `ps1`                            | `powershell` |    894,737 |  3.602 MB | [91.96%](../packs/powershell/model/BENCHMARKS.md) — exposed 3-file regression                                                       |
| [BAT / CMD](../packs/bat/model/README.md)                      | `bat`, `cmd`                                           | `bat`        |    894,350 |  3.600 MB | [90.61%](../packs/bat/model/BENCHMARKS.md) — exposed 3-file regression; additional 6 files 75.36% (separate cohort)                 |
| [Assembly](../packs/assembly/model/README.md)                  | `assembly`, `asm`, `nasm`, `masm`, `gas`               | `assembly`   |    893,711 |  3.597 MB | [98.63%](../packs/assembly/model/BENCHMARKS.md) — natural test, 5 files; per-profile results in report                              |
| [Java](../packs/java/model/README.md)                          | `java`                                                 | `java`       |    895,382 |  3.604 MB | [93.59%](../packs/java/model/BENCHMARKS.md) — exposed 29-file regression                                                            |
| [C#](../packs/csharp/model/README.md)                          | `csharp`, `cs`, `c#`                                   | `csharp`     |    895,511 |  3.605 MB | [95.53%](../packs/csharp/model/BENCHMARKS.md) — exposed 24-file regression                                                          |
| [C](../packs/c/model/README.md)                                | `c`                                                    | `c`          |    894,227 |  3.599 MB | [94.60%](../packs/c/model/BENCHMARKS.md) — exposed 18-file regression                                                               |
| [C++](../packs/cpp/model/README.md)                            | `cpp`, `c++`, `cxx`                                    | `cpp`        |    895,511 |  3.605 MB | [94.16%](../packs/cpp/model/BENCHMARKS.md) — exposed 14-file regression                                                             |
| [PHP](../packs/php/model/README.md)                            | `php`                                                  | `php`        |    895,898 |  3.606 MB | [95.55%](../packs/php/model/BENCHMARKS.md) — exposed 21-file regression                                                             |
| [Svelte](../packs/svelte/model/README.md)                      | `svelte`                                               | `svelte`     |    895,398 |  3.607 MB | [91.41%](../packs/svelte/model/BENCHMARKS.md) — exposed 9-file regression                                                           |
| [Rust](../packs/rust/model/README.md)                          | `rust`, `rs`                                           | `rust`       |    895,511 |  3.605 MB | [95.93%](../packs/rust/model/BENCHMARKS.md) — exposed 15-file regression                                                            |
| [Zig](../packs/zig/model/README.md)                            | `zig`                                                  | `zig`        |    894,485 |  3.600 MB | [93.65%](../packs/zig/model/BENCHMARKS.md) — exposed 21-file regression                                                             |
| [Dart / Flutter](../packs/dart/model/README.md)                | `dart`, `flutter`                                      | `dart`       |    894,872 |  3.602 MB | [95.07%](../packs/dart/model/BENCHMARKS.md) — exposed 20-file regression                                                            |
| [Swift](../packs/swift/model/README.md)                        | `swift`                                                | `swift`      |    894,872 |  3.602 MB | [94.52%](../packs/swift/model/BENCHMARKS.md) — exposed 22-file regression                                                           |
| [Kotlin](../packs/kotlin/model/README.md)                      | `kotlin`, `kt`, `kts`, `kotlin-script`                 | `kotlin`     |    895,640 |  3.605 MB | [96.28%](../packs/kotlin/model/BENCHMARKS.md) — exposed 31-file regression                                                          |
| [R](../packs/r/model/README.md)                                | `r`                                                    | `r`          |    894,872 |  3.602 MB | [96.04%](../packs/r/model/BENCHMARKS.md) — natural test, 15 files                                                                   |
| [Scala](../packs/scala/model/README.md)                        | `scala`                                                | `scala`      |    895,656 |  3.608 MB | [90.23%](../packs/scala/model/BENCHMARKS.md) — exposed 30-file regression                                                           |
| [Ruby](../packs/ruby/model/README.md)                          | `ruby`, `rb`, `rake`, `gemspec`, `gemfile`, `rakefile` | `ruby`       |    895,656 |  3.608 MB | [90.60%](../packs/ruby/model/BENCHMARKS.md) — exposed 15-file regression; additional 11 files 94.41% (separate cohort)              |
| [Lua](../packs/lua/model/README.md)                            | `lua`                                                  | `lua`        |    895,640 |  3.605 MB | [94.36%](../packs/lua/model/BENCHMARKS.md) — exposed 15-file regression                                                             |
| [GraphQL](../packs/graphql/model/README.md)                    | `graphql`, `gql`                                       | `graphql`    |    895,124 |  3.603 MB | [96.36%](../packs/graphql/model/BENCHMARKS.md) — 14 natural test files                                                              |

## File formats

[Full support details and measured limits](file-formats.md).

| Name                                                  | Accepted content IDs / aliases                            | Model        | Parameters | ONNX size | Measured test exact-span F1                                                                                         |
| ----------------------------------------------------- | --------------------------------------------------------- | ------------ | ---------: | --------: | ------------------------------------------------------------------------------------------------------------------- |
| [JSON / JSONC](../packs/json/model/README.md)         | `json`, `jsonc`                                           | `json`       |    894,872 |  3.602 MB | [Natural test](../packs/json/model/BENCHMARKS.md): JSON 99.71% (9 files); JSONC 99.84% (6 files)                    |
| [YAML](../packs/yaml/model/README.md)                 | `yaml`, `yml`                                             | `yaml`       |    894,872 |  3.602 MB | [95.34%](../packs/yaml/model/BENCHMARKS.md) — natural test, 12 files                                                |
| [TOML](../packs/toml/model/README.md)                 | `toml`                                                    | `toml`       |    894,872 |  3.602 MB | [99.10%](../packs/toml/model/BENCHMARKS.md) — natural test, 9 files                                                 |
| [INI](../packs/ini/model/README.md)                   | `ini`, `cfg`, `editorconfig`                              | `ini`        |    894,872 |  3.602 MB | [96.93%](../packs/ini/model/BENCHMARKS.md) — exposed 8-file regression                                              |
| [.env](../packs/dotenv/model/README.md)               | `dotenv`, `env`, `.env`                                   | `dotenv`     |    894,872 |  3.602 MB | [98.25%](../packs/dotenv/model/BENCHMARKS.md) — natural test, 3 files                                               |
| [XML](../packs/xml/model/README.md)                   | `xml`                                                     | `xml`        |    894,108 |  3.601 MB | [87.72%](../packs/xml/model/BENCHMARKS.md) — exposed 7-file regression                                              |
| [SVG](../packs/xml/model/README.md)                   | `svg`                                                     | `xml`        |    894,108 |  3.601 MB | [100.00%](../packs/xml/model/BENCHMARKS.md) — exposed 6-file regression                                             |
| [Markdown](../packs/markdown/model/README.md)         | `markdown`, `md`, `mdown`, `mkd`                          | `markdown`   |    894,227 |  3.599 MB | [95.10%](../packs/markdown/model/BENCHMARKS.md) — new independent natural test, 20 files                            |
| [Dockerfile](../packs/dockerfile/model/README.md)     | `dockerfile`, `docker`, `containerfile`                   | `dockerfile` |    893,969 |  3.598 MB | [96.33%](../packs/dockerfile/model/BENCHMARKS.md) — independent natural test, 14 files                              |
| [Makefile](../packs/makefile/model/README.md)         | `makefile`, `make`, `mk`, `mak`, `gnumake`, `gnumakefile` | `makefile`   |    894,479 |  3.601 MB | [94.12%](../packs/makefile/model/BENCHMARKS.md) — exposed 17-file regression; historical additional 16 files 94.57% |
| [Protocol Buffers](../packs/protobuf/model/README.md) | `protobuf`, `proto`, `protocol-buffers`                   | `protobuf`   |    894,995 |  3.603 MB | [98.55%](../packs/protobuf/model/BENCHMARKS.md) — 12 fresh natural test files                                       |
| [Diff / Patch](../packs/diff/model/README.md)         | `diff`, `patch`, `udiff`, `unified-diff`, `git-diff`      | `diff`       |    893,963 |  3.599 MB | [98.03%](../packs/diff/model/BENCHMARKS.md) — 26 natural test patches                                               |

The 2026-11-19 revisions report exposed historical regressions separately from
additional frozen-family tests. Targets of 90%/95% are goals, not guarantees:
Perl's additional namespace files and BAT's harder project holdout remain below
90%. See each report's role macro, Golden and dialect details. Earlier complete
inference bundles remain under `packs/<name>/model-20261119-v1` and the matching
browser archives; external data and full training experiments remain preserved.
Selected overlapping windows can improve long-file edges with additional browser
inference cost; short snippets keep the existing single-window path.

Previously recorded HTML/Vue/PHP/Markdown composed scores refer to their archived
child-model revisions. A changed JS/TS child requires a new composed measurement;
base-model scores and browser/native consistency are separate evidence.
