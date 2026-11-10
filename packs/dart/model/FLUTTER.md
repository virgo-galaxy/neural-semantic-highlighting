# Flutter source highlighting

Flutter has a dedicated Playground entry, icon and eight examples. Source files
are still .dart; the public Flutter alias uses the same selected Dart weights,
schema and 512-byte inference context. The project still has 22 model packs.
No Dart/Flutter SDK, analyzer, pub environment or framework runtime is installed.

    const { html } = await highlighter.highlight(source, { language: "flutter" });

For a selective build:

    import { createHighlighter } from "@nsh/highlighter/core";
    import flutter from "@nsh/highlighter/languages/flutter";
    import "@nsh/highlighter/theme.css";

    const highlighter = createHighlighter({ languages: [flutter] });
    const { html } = await highlighter.highlight(source, { language: "flutter" });

The Flutter module re-exports the Dart descriptor. Registering either or both
uses one model asset. Both names work; Flutter normalizes to Dart, so returned
language, semantic offsets and HTML data-language are canonical Dart. Existing
Dart CSS overrides and all light/dark presets apply. A language-flutter code
element works through highlightElement. No new extension or automatic framework
detection is introduced.

## Evidence and decision

The already selected Dart model scores **93.95% exact-span F1** on 48 additional
application files across twelve pinned official Flutter sample projects. Role
macro F1 is **76.03%**. Exact/lexical/normalized-shape checks find no matching
files in prior Dart Gold. This is additional source review, without model
training or tuning; it is separate from the historical Dart test score.

| Application family     | Exact-span F1 |
| ---------------------- | ------------: |
| animations             |        95.21% |
| compass_app            |        94.62% |
| cupertino_gallery      |        95.39% |
| date_planner           |        93.81% |
| desktop_photo_search   |        92.56% |
| dynamic_theme          |        92.38% |
| form_app               |        94.32% |
| material_3_demo        |        94.28% |
| navigation_and_routing |        95.74% |
| platform_design        |        91.78% |
| testing_app            |        95.16% |
| web_embedding          |        93.96% |

Eight independently authored displayed examples aggregate **95.73%**:

| Example         | Exact-span F1 |
| --------------- | ------------: |
| animation.dart  |        95.27% |
| builders.dart   |        96.93% |
| forms.dart      |        93.87% |
| hello.dart      |        98.48% |
| inherited.dart  |        95.70% |
| lists.dart      |        93.17% |
| navigation.dart |        96.09% |
| stateful.dart   |        96.40% |

They cover widget trees, themes, State/setState and lifecycle, FutureBuilder and
untyped callbacks, forms/controllers/disposal, navigation and mounted checks,
slivers/record bindings, animations/mixins and inherited/listenable state.
Examples have independent grammar/coverage checks, not SDK compilation.

The offline teacher passes eight separately hand-marked Flutter cases, alongside
the unchanged 35 Dart cases, across twelve tests. The neural model is completely
exact in **0/8** new marked cases when every boundary, role and declaration flag
must match; these strict visible diagnostics and role macro scores retain the
remaining errors despite high application/display span F1. No runtime parser or
source-spelling repair hides them.

Given this bounded evidence, Flutter reuses the existing model without retraining.
Native/ONNX weights and every earlier dataset/checkpoint remain preserved.
[Application review](reports/flutter/real-applications.json),
[display/Golden diagnostics](reports/flutter/challenges.json) and
[decision](reports/flutter/decision.json) record the original results.

## Limits

Constructor/function/method distinctions, local/property/parameter roles, generic
and pattern scopes, literal boundaries and declaration flags retain the existing
[Dart limits](KNOWN_ISSUES.md). Unknown imported widget calls use syntactic roles;
names and named arguments are not resolved against Flutter APIs or dependencies.
Package versions, generated code, analyzer validity and complete SDK compatibility
are not certified. State-management/package-specific DSLs receive Dart syntax
highlighting without executing code or resolving a framework project.

The source recipe is pinned in ../dataset/flutter-examples.json; original text,
Git blobs and the complete upstream license remain under the established external
Dart dataset root. Review files and Golden/Playground are excluded from training.
The [official forms](https://docs.flutter.dev/cookbook/forms) and
[navigation](https://docs.flutter.dev/cookbook/navigation) documentation guided
the authored examples; the existing independent Dart CST provides labels.
