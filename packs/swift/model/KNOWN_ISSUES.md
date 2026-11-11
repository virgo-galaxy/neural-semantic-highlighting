# Swift known issues

A useful bounded source-display baseline with independent official parser Gold.

- Natural test exact-span F1 is 93.65%
  across 22 files; role macro F1 is 85.01%.
  Small source-family holdouts and six projects do not establish universal Swift
  or SDK/framework compatibility.
- Mixed displayed raw, multi-line, continued, regex and interpolated strings score
  79.79%.
  Delimiters, interpolation punctuation and neighboring content can split or
  exchange roles, even when adjacent pieces look similarly colored. Long comments
  and dollar names (`$0`, `$title`) can also have incorrect boundaries.
- Unknown imported calls stay syntactic functions, without capitalization or
  dependency-resolution heuristics. Constructor/function/method, enum/type/generic,
  argument-label and local parameter/property/variable roles remain approximate.
  Declaration flags can be wrong even where the visible color is acceptable.
- Condition/guard bindings, deeply nested closures/patterns, generated wrapper
  members, imported associated types, overloads and distant symbols are not fully
  resolved. SwiftUI shares Swift syntax and weights; no framework API validation,
  result-builder execution, macro expansion, availability checking or project
  type analysis occurs during supervision or neural inference.
- The independent teacher passes 28 cases and 12 tests; neural output is entirely
  exact in 13/28 Golden cases. Display/inspected-validation evidence is
  development data, distinct from the first natural test.
- Official SwiftParser 6.4.2 accepts the bounded modern forms. All historical,
  experimental or future syntax, compiler language modes and SDK combinations
  are not certified. Six display files typecheck on 6.4.2; two SwiftUI samples
  additionally typecheck on preserved Xcode 6.0.3/SDK 15.2 because the current CLI
  SDK has no SwiftUIMacros State plugin. No plugin or SDK is installed here.
- The unchanged 512-byte context limits long literal/comment continuity and distant
  declarations. Browser/native parity preserves learned predictions and original
  text; it does not prove semantic perfection. No runtime scanner or parser repairs
  prediction errors. Frontend consumers need no Swift, Xcode or Python process.

Every previous corpus, Gold/prepared snapshot, experiment, full checkpoint and
formal language model remains preserved. Resume full artifacts/swift checkpoints,
never inference-only .pt or ONNX files.
