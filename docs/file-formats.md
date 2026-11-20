# File formats

[Back to the integration guide](../README.md) · [Content organization](content-organization.md)

Data/configuration, markup/documents, engineering files and interface descriptions.
These use the same highlighter API and theme system as code languages.

## Names and models

<!-- catalog:start -->

| Name       | Content ID   | Accepted aliases                              | Model / direct dependencies |
| ---------- | ------------ | --------------------------------------------- | --------------------------- |
| JSON       | `json`       | —                                             | `json`                      |
| JSONC      | `jsonc`      | —                                             | `json`                      |
| YAML       | `yaml`       | `yml`                                         | `yaml`                      |
| TOML       | `toml`       | —                                             | `toml`                      |
| INI        | `ini`        | `cfg`, `editorconfig`                         | `ini`                       |
| .env       | `dotenv`     | `env`, `.env`                                 | `dotenv`                    |
| XML        | `xml`        | —                                             | `xml`                       |
| SVG        | `svg`        | —                                             | `xml`                       |
| Markdown   | `markdown`   | `md`, `mdown`, `mkd`                          | `markdown`                  |
| Dockerfile | `dockerfile` | `docker`, `containerfile`                     | `dockerfile`                |
| Makefile   | `makefile`   | `make`, `mk`, `mak`, `gnumake`, `gnumakefile` | `makefile`                  |
| Protobuf   | `protobuf`   | `proto`, `protocol-buffers`                   | `protobuf`                  |
| Diff/Patch | `diff`       | `patch`, `udiff`, `unified-diff`, `git-diff`  | `diff`                      |

<!-- catalog:end -->

## Measured quality and support boundaries

Exact-span F1 requires the token start, end and type to match. Different test sets
and sample sizes are not directly comparable. Historical measurements below are
retained; classification does not change the models or scores.

| Name                                                  | Supported source / file extensions                                                                                                                                                  | Measured test exact-span F1                                                                                         | Current state / measured limits                                                                                                          |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| [JSON / JSONC](../packs/json/model/README.md)         | `.json`, `.jsonc`, `.code-workspace`; strict JSON and explicit JSONC comments/trailing commas; quoted keys/values and nested data                                                   | [Natural test](../packs/json/model/BENCHMARKS.md): JSON 99.71% (9 files); JSONC 99.84% (6 files)                    | Browser + local, one shared model; [literal/comment boundaries and key/value roles](../packs/json/model/KNOWN_ISSUES.md) remain limited  |
| [YAML](../packs/yaml/model/README.md)                 | YAML .yaml/.yml configuration, YAML 1.2 Core scalars, mappings/sequences, quoted/block strings, anchors/aliases, tags, directives and multi-document streams                        | [95.34%](../packs/yaml/model/BENCHMARKS.md) — natural test, 12 files                                                | Browser + local; [measured scalar/structure roles and boundaries](../packs/yaml/model/KNOWN_ISSUES.md) remain limited                    |
| [TOML](../packs/toml/model/README.md)                 | TOML .toml configuration, common 1.0 forms and tested 1.1 additions, tables/array tables, dotted/quoted keys, arrays/inline tables, four string and date/time forms                 | [99.10%](../packs/toml/model/BENCHMARKS.md) — natural test, 9 files                                                 | Browser + local; [measured scalar/structure roles and boundaries](../packs/toml/model/KNOWN_ISSUES.md) remain limited                    |
| [INI](../packs/ini/model/README.md)                   | INI .ini/.cfg and EditorConfig source, sections/root options, =/: key-value delimiters, full-line comments, duplicates, empty/valueless options and indented continuations          | [96.93%](../packs/ini/model/BENCHMARKS.md) — exposed 8-file regression                                              | Reviewed browser + local; [measured limits](../packs/ini/model/KNOWN_ISSUES.md) and dialect/cohort differences remain                    |
| [.env](../packs/dotenv/model/README.md)               | Common .env/.env.* dotenv configuration, variable declarations, export, plain/single/double/backtick and multiline string values, hash comments, empty values and opaque references | [98.25%](../packs/dotenv/model/BENCHMARKS.md) — natural test, 3 files                                               | Browser + local; [measured scalar/structure roles and boundaries](../packs/dotenv/model/KNOWN_ISSUES.md) remain limited                  |
| [XML](../packs/xml/model/README.md)                   | .xml, .xsd, .xsl/.xslt, .plist, .csproj/.props/.targets; XML 1.0 source                                                                                                             | [87.72%](../packs/xml/model/BENCHMARKS.md) — exposed 7-file regression                                              | Reviewed browser + local; [measured limits](../packs/xml/model/KNOWN_ISSUES.md) and dialect/cohort differences remain                    |
| [SVG](../packs/xml/model/README.md)                   | .svg; paths, shapes, groups, gradients, filters, animation and accessible text; XML 1.0 source                                                                                      | [100.00%](../packs/xml/model/BENCHMARKS.md) — exposed 6-file regression                                             | Reviewed browser + local; [measured limits](../packs/xml/model/KNOWN_ISSUES.md) and dialect/cohort differences remain                    |
| [Markdown](../packs/markdown/model/README.md)         | Markdown/GFM source, headings, lists/tasks, tables, links/references, nested emphasis, code, opaque HTML/front matter and predicted top-level fenced regions                        | [95.10%](../packs/markdown/model/BENCHMARKS.md) — new independent natural test, 20 files                            | Optimized browser/local model; [strict edge cases and long fenced bodies](../packs/markdown/model/KNOWN_ISSUES.md) remain weaker         |
| [Dockerfile](../packs/dockerfile/model/README.md)     | Dockerfile/Containerfile, multistage names, ARG/ENV/LABEL, flags, Shell/JSON forms, continuations and heredocs                                                                      | [96.33%](../packs/dockerfile/model/BENCHMARKS.md) — independent natural test, 14 files                              | Browser + local; [Unicode comments, long strings and source-local shell roles](../packs/dockerfile/model/KNOWN_ISSUES.md) remain limited |
| [Makefile](../packs/makefile/model/README.md)         | Makefile/GNUmakefile, .mk/.mak; common GNU Make targets, variables/functions, directives, opaque define values and Shell recipes                                                    | [94.12%](../packs/makefile/model/BENCHMARKS.md) — exposed 17-file regression; historical additional 16 files 94.57% | Reviewed browser + local; [measured limits](../packs/makefile/model/KNOWN_ISSUES.md) and dialect/cohort differences remain               |
| [Protocol Buffers](../packs/protobuf/model/README.md) | Source definitions; `.proto`, proto2/proto3 and grammar-supported editions                                                                                                          | [98.55%](../packs/protobuf/model/BENCHMARKS.md) — 12 fresh natural test files                                       | Browser + local; [long comments, option roles and compiler-validation scope](../packs/protobuf/model/KNOWN_ISSUES.md) remain limited     |
| [Diff / Patch](../packs/diff/model/README.md)         | Unified and Git patch source; `.diff`, `.patch`                                                                                                                                     | [98.03%](../packs/diff/model/BENCHMARKS.md) — 26 natural test patches                                               | Browser + local; [long-line roles, unusual metadata and unsupported diff formats](../packs/diff/model/KNOWN_ISSUES.md) remain limited    |
