# Go Pack Coverage Policy

This document defines the language-version support window, feature-coverage policy, and
training/evaluation expectations for the Go language pack.

It complements `SEMANTICS.md`:

- `SEMANTICS.md` defines how source spans are labeled.
- `COVERAGE.md` defines which Go language eras and features the pack is expected to learn,
  exercise, and verify.

This file is a coverage ledger, not a claim that every listed item is already implemented.
A feature is considered supported only after the relevant training and evaluation evidence exists.

## Support window

The targeted language window begins at **Go 1.18** and currently extends through **Go 1.27.x**.

```text
Minimum targeted language era: Go 1.18
Current target family:         Go 1.27.x
```

Go 1.18 is the practical lower bound because it introduced type parameters, parameterized types
and functions, type sets, union elements, `~T`, `any`, and `comparable`. These changes define the
modern Go language surface that the pack is intended to understand.

The pack does not deliberately train for pre-1.18 language-version compatibility. Syntax and
constructs that originated before Go 1.18 but remain normal, valid modern Go are still part of the
core corpus and remain fully in scope.

Examples of such core constructs include packages, imports, functions, methods, structs,
interfaces, embedding, channels, goroutines, `defer`, `select`, type switches, type assertions,
labels, composite literals, function types, and variadic functions.

## Coverage model

Training should not weight every Go release equally.

The corpus is organized conceptually into three layers:

1. **Core modern Go**
   - The largest share of training data.
   - Real-world code using language constructs that remain common across Go 1.18+ projects.
   - Includes older constructs that are still ordinary modern Go.

2. **Version-focused curriculum**
   - Targeted examples for language features introduced or materially changed from Go 1.18
     onward.
   - Ensures rare or newly introduced legal syntax is not left to random corpus frequency.
   - A release receives focused data only when its changes matter to source-level semantic
     highlighting or Gold labeling.

3. **Semantic hard cases**
   - Ambiguous, context-sensitive, or easily fragmented constructs.
   - Used for focused training, challenges, diagnostics, and held-out evaluation.
   - Added from observed model failures rather than from version numbers alone.

Natural corpus distribution should teach real Go usage. Focused curriculum should guarantee
coverage of rare but important language capabilities.

## Go language evolution timeline

The table below tracks language changes from the minimum supported era through the current target.
It intentionally distinguishes language evolution from changes that materially affect semantic
highlighting.

| Go version | Language changes relevant to this pack                                                                                                         | Coverage expectation                                                                                                                                                                        |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1.18**   | Type parameters; parameterized functions and types; type sets; union elements; `~T`; `any`; `comparable`                                       | **Foundation milestone. Heavy coverage required.** Generics and constraints must be present in ordinary corpus, focused fixtures, challenges, and evaluation.                               |
| **1.19**   | Small correction to the scope of type parameters in method declarations                                                                        | Parser/type-checker and Gold-labeler compatibility required. No large dedicated model curriculum unless failures show a need.                                                               |
| **1.20**   | Slice-to-array conversions; broader satisfaction of `comparable` constraints                                                                   | Include representative examples. Mostly type-system coverage rather than a new highlighting vocabulary.                                                                                     |
| **1.21**   | New predeclared built-ins `min`, `max`, and `clear`; broader generic function type inference                                                   | Built-ins require explicit semantic coverage as `function` + `default-library`. Type-inference cases should exercise the Gold labeler and contextual model behavior.                        |
| **1.22**   | Per-iteration loop variables; `range` over integers                                                                                            | Integer range requires focused syntax coverage. Per-iteration identity is primarily a symbol-resolution change and does not require a new highlighting role.                                |
| **1.23**   | `range` over iterator functions; preview support for generic type aliases                                                                      | Range-over-function requires focused coverage. Generic type aliases are targeted through their stable Go 1.24 form rather than depending on preview-only behavior.                          |
| **1.24**   | Generic type aliases become fully supported                                                                                                    | **Focused coverage required.** Include declarations, references, constraints, nested instantiations, and alias-heavy ambiguity cases.                                                       |
| **1.25**   | No language changes affecting Go programs                                                                                                      | No release-specific curriculum required solely for version completeness.                                                                                                                    |
| **1.26**   | `new` accepts an expression; generic types may refer to themselves in their own type parameter lists                                           | **Focused coverage required.** Exercise expression-valued `new` and recursive/self-referential generic constraints.                                                                         |
| **1.27**   | Generic methods; struct literal keys may use valid field selectors; generic function type inference is generalized to more assignment contexts | **High-priority focused coverage required.** Generic methods are a major new syntax/semantic boundary and must receive dedicated fixtures, curriculum, challenges, and held-out evaluation. |

## Required feature families

The following feature families define the intended modern Go language surface. They should be used
as a checklist when building fixtures, corpus reports, focused datasets, challenges, and evaluation
sets.

### Core language

- [ ] package clauses and imports
- [ ] constants and variables
- [ ] short variable declarations
- [ ] functions and named result parameters
- [ ] methods and receivers
- [ ] structs and fields
- [ ] interfaces and interface methods
- [ ] embedding and promoted members
- [ ] pointers
- [ ] arrays and slices
- [ ] maps
- [ ] channels
- [ ] goroutines and `go` statements
- [ ] `defer`
- [ ] `select`
- [ ] switches and type switches
- [ ] type assertions
- [ ] labels, `break`, `continue`, and `goto`
- [ ] composite literals
- [ ] anonymous structs
- [ ] function types and closures
- [ ] variadic functions
- [ ] rune, string, numeric, and imaginary literals
- [ ] comments and directives relevant to source parsing

### Modern generics baseline - Go 1.18+

- [ ] generic functions
- [ ] generic types
- [ ] type parameter declarations
- [ ] type parameter references
- [ ] explicit type arguments
- [ ] inferred type arguments
- [ ] `any`
- [ ] `comparable`
- [ ] type sets
- [ ] union constraint elements
- [ ] approximation elements using `~T`
- [ ] generic interfaces used as constraints
- [ ] nested generic instantiations
- [ ] generic receiver types

### Version-focused modern Go

- [ ] Go 1.20 slice-to-array conversions
- [ ] Go 1.20 broader `comparable` constraint cases
- [ ] Go 1.21 `min`, `max`, and `clear`
- [ ] Go 1.21 expanded generic function inference
- [ ] Go 1.22 range over integers
- [ ] Go 1.23 range over iterator functions
- [ ] Go 1.24 generic type aliases
- [ ] Go 1.26 `new(expression)`
- [ ] Go 1.26 self-referential generic type constraints
- [ ] Go 1.27 generic methods
- [ ] Go 1.27 selector-style struct literal keys
- [ ] Go 1.27 generalized generic function assignment inference

## Evidence model

A feature appearing in this document does not by itself make the feature "supported".

Coverage should eventually be tracked across the following evidence layers:

| Evidence layer      | Meaning                                                                         |
| ------------------- | ------------------------------------------------------------------------------- |
| Semantic contract   | The existing NSH token types and modifiers can represent the feature correctly. |
| Gold fixture        | A deterministic labeled example exists and is validated.                        |
| Natural corpus      | The feature occurs in real collected Go source.                                 |
| Focused curriculum  | Targeted training examples exist when natural frequency is insufficient.        |
| Challenge           | Dedicated difficult or ambiguity-oriented tests exist where appropriate.        |
| Held-out evaluation | Unseen examples demonstrate the selected model handles the feature acceptably.  |

The long-term coverage matrix should be maintained as evidence is added. Do not mark an item as
complete merely because the parser accepts it or because one example highlights correctly.

## Corpus policy

The first Go model should prefer a compact, high-quality corpus over indiscriminate scale.

Recommended source layers are:

1. the current target Go standard library source;
2. official Go Project repositories under `golang.org/x/...`;
3. representative real-world modules from multiple domains;
4. curated focused examples for low-frequency modern language features.

For ecosystem-scale collection, prefer Go-native module metadata and module archives where
practical rather than assuming the TypeScript GitHub collection strategy must be reused unchanged.

A future collector may use the Go Module Index and module proxy flow:

```text
Go Module Index
  -> module/version
  -> GOPROXY
  -> module archive
  -> .go source files
```

The initial baseline should remain intentionally small enough to inspect. Before increasing corpus
size, report at least:

- generated 512-byte adaptive windows;
- token-type distribution;
- modifier distribution;
- rare semantic-role counts;
- coverage of the version-focused feature families in this document.

## Training policy

The initial Go model should start with the established NSH baseline of **512 UTF-8 bytes** of model
context.

Do not increase context merely because newer Go syntax is more expressive. Increase it only when
challenge failures and error analysis demonstrate that missing context is the actual bottleneck.

Version-focused data should be mixed with the main training stream rather than used as a late,
aggressive fine-tune that risks degrading ordinary Go behavior.

The exact sampling ratio is an empirical training decision and is intentionally not fixed in this
document.

## Unsupported and intentionally unlearned areas

The following are outside the deliberate version-coverage target:

- dedicated compatibility training for Go versions earlier than 1.18;
- obsolete historical syntax that is not valid modern Go;
- preview or experimental syntax that never became part of the supported language;
- version-specific toolchain, runtime, or standard-library changes that do not affect source-level
  semantic highlighting;
- framework- or domain-specific semantics that belong above the Go language pack;
- cross-file symbol intelligence, rename/find-references behavior, or whole-program analysis.

This policy does **not** exclude syntax invented before Go 1.18 when that syntax remains ordinary
and valid in current Go code.

## Release maintenance rule

When a new stable Go release is published:

1. review the official release notes and language specification changes;
2. add the release to the timeline in this file;
3. classify each language change as one of:
   - no highlighting impact;
   - Gold-labeler/type-checker compatibility only;
   - ordinary corpus coverage;
   - focused curriculum required;
4. add or update fixtures before training on the new capability;
5. add challenges for ambiguity-prone or low-frequency features;
6. update held-out evaluation before claiming support for the new release family.

A new release should not be considered covered merely because the current compiler can parse it.

## Official references

- Go 1.18 release notes: <https://go.dev/doc/go1.18>
- Go 1.19 release notes: <https://go.dev/doc/go1.19>
- Go 1.20 release notes: <https://go.dev/doc/go1.20>
- Go 1.21 release notes: <https://go.dev/doc/go1.21>
- Go 1.22 release notes: <https://go.dev/doc/go1.22>
- Go 1.23 release notes: <https://go.dev/doc/go1.23>
- Go 1.24 release notes: <https://go.dev/doc/go1.24>
- Go 1.25 release notes: <https://go.dev/doc/go1.25>
- Go 1.26 release notes: <https://go.dev/doc/go1.26>
- Go 1.27 release notes: <https://go.dev/doc/go1.27>
