# Dart baseline evaluation

Exact-span F1 requires original UTF-16 start, end and semantic role to match.
Role macro F1 averages represented roles; declaration modifiers are separate.
This measures independent CST/source-local roles, not the official analyzer,
project type checking, SDK-version compatibility or Flutter widget semantics.
No Dart/Flutter SDK is installed or used, including for the displayed examples.

| Evidence           | Documents | Exact-span F1 | Role macro F1 |
| ------------------ | --------: | ------------: | ------------: |
| Natural validation |        23 |        95.01% |        78.82% |
| Focus validation   |       136 |        96.46% |        91.86% |
| First natural test |        20 |        94.22% |        82.21% |
| First focus test   |       131 |        93.30% |        89.07% |

Frozen full candidate: artifacts/dart/context512-literals-20261110-01/candidates/epoch-0006.pt, epoch 6 of the literal revision.
Fixed natural validation role macro F1 (0.7537)
selects within that run. Actual natural validation source, independent Golden
and eight displays were reviewed before freeze and first adaptive test.
No training followed that test; these results are now known for future revisions.
Combined natural/focus scores are not substituted for real-source accuracy.

## Corpus and source-family audit

Snapshot: acbf9e90af51271b3a1e9e956a2de65da2c8f341ae34949b491717ae0d63b6a9. 1,724 input records,
111 exact duplicates merged,
0 cross-family copy records excluded,
1,613 retained. Exact/lexical/normalized copy auditing
precedes windowing. All 94 initial package/module/task assignments remain intact;
the literal revision extends the frozen map to 102 before training.

The capture pins 80 official Dart core-package files, 60 HTTP-package files and
72 stable Flutter files with immutable Git blobs, original bytes and complete
licenses/notices. The initial 1,320 original tasks cover 55 intact families;
192 added literal/context tasks cover eight new families. The final 1,724 records
pass the pinned grammar and original coverage: zero quarantines in this bounded
capture, not a universal Dart syntax claim. Golden and Playground are excluded.
Natural validation includes async, web_socket and Cupertino source. Project
diversity and small held-out family/sample counts limit generalization claims.

| Split      | Natural docs | Focus docs | Windows |
| ---------- | -----------: | ---------: | ------: |
| train      |          169 |       1134 |    3031 |
| validation |           23 |        136 |     371 |
| test       |           20 |        131 |     362 |

Original sources/licenses, all corpus/Gold/prepared revisions and all full runs
remain under ~/Datasets/neural-semantic-highlighting/dart and artifacts/dart.
No previous language data, experiment or native/browser model is replaced.

## Environment, Gold and bounded training

No Dart/Flutter SDK, analyzer, pub environment or global dependency is installed.
Tree-sitter 0.25.10 and nielsenko/tree-sitter-dart 0.3.0 at immutable commit
cc75f92b34037bcdbc05b12b0db7fe20677306c1 provide the independent grammar.
Existing Apple Clang builds original pinned C sources into ignored project cache;
source, compiler and library hashes stay in reports/teacher-tools.json.
This parser never evaluates Dart, annotations, generators, imports or project
configuration. Missing/error/unmapped syntax and incomplete coverage fail closed.
No compiler-validity claim is made for authored or upstream source.

The model has **894,872 parameters**, four layers, width 128, four heads,
FFN 512 and **512 original UTF-8 bytes** of context. A smoke run precedes three
initial epochs transferred from the compatible full C# checkpoint
artifacts/csharp/context512-mixed-20261109-01/candidates/epoch-0003.pt.
Review caught untyped closure formals, nested local functions and callback-type
parameter scope differences in Gold. Those were corrected without altering old
snapshots; the preserved full initial Dart epoch-3 candidate initializes a fresh
literal run. Additional short epochs and optimizer/RNG continuation are recorded
exactly in reports/experiments.json. Selected epoch need not be the last epoch.
Inference .pt/ONNX files are never training initializers.

## Actual code and independent probes

Eight original displayed examples aggregate 89.36%
exact-span F1. The Flutter widget example scores 96.85%; mixed strings
score 85.34%. These are visible development examples, not unseen scores.
Ten real validation files were read directly; F1 ranges 94.38%–99.15%.

| Display example  | Exact-span F1 |
| ---------------- | ------------: |
| async.dart       |        90.77% |
| classes.dart     |        92.11% |
| collections.dart |        88.37% |
| hello.dart       |        88.31% |
| modern.dart      |        87.25% |
| patterns.dart    |        86.03% |
| strings.dart     |        85.34% |
| widgets.dart     |        96.85% |

Neural output exactly matches all spans/roles/modifiers in 6/35
Golden cases. The separate offline teacher passes all 35 manually
marked cases and eleven tests. Missing/unexpected spans remain in reports.
Raw/triple/interpolated literal boundaries, inferred/local names, constructors,
pattern scopes and declaration flags retain controlled errors. No runtime parser,
delimiter scanner or source-spelling repair hides these limitations.

The grammar accepts bounded modern records/patterns, class modifiers, extension
types, null-aware elements, dot shorthands and primary-constructor forms. This
does not certify every feature of any SDK release. Flutter shares Dart syntax;
imported widgets, types, generated code and package semantics are not resolved.
Browser/native parity verifies consistent learned output and source preservation,
not perfect semantic accuracy.
