# PHP known issues

A usable baseline with bounded syntax/local-scope supervision. Read
[BENCHMARKS.md](BENCHMARKS.md) for separate natural/focus/base/composed evidence;
base PHP/region F1 does not describe whole-template accuracy.

- Double-quoted/interpolated strings, heredoc/nowdoc delimiters and long literal
  content can split or acquire wrong boundaries. The visible heredoc probe is
  90.91% exact-span F1; parameter/property roles inside interpolations can be wrong.
- Local variables, captured values, parameters, enum/type references, named argument
  names and callables may exchange roles. Tagless closure source remains weaker
  than the simple tagged greeting example. Declaration modifiers are independent
  predictions and can be wrong with otherwise correct visible colors.
- The complete PHP/HTML template probes are 95.50% and 87.69% exact-span F1.
  They are visible development diagnostics, not an unseen template test. Incorrect
  PHP-predicted HTML boundaries and incomplete fragments limit child HTML/JS/CSS
  inference. Region errors are not repaired by a runtime parser/tag scanner.
- PHP inserted inside HTML attributes or JS/CSS string bodies, arbitrary template
  dialects, Blade/Twig, optional short `<?` tags and every newest PHP feature are
  not certified. Three captured Blade files were quarantined and preserved.
- The teacher does not load PHP projects, Composer dependencies or autoloaders;
  inheritance, dynamic variables/calls, runtime class aliases, reflection, namespace
  imports and whole-project type resolution remain approximate. DocBlocks stay
  comments, including generics/annotations. Regex contents stay string syntax.
- Five of 23 visible neural Golden cases match every boundary, role and modifier
  exactly; the offline teacher separately passes all 23 independently marked cases.
  Ten natural validation probes range from 81.82%–100% exact-span F1; framework
  compiler/embedded-code construction remains weaker than straightforward classes.
- The unchanged 512-byte context bounds long comments/literals/HTML regions and
  distant bindings. Long code uses multiple predicted windows without Gold cuts.
  Browser parity establishes consistency with this native model, not perfection.

No PHP interpreter/SDK, Composer, server or global package was installed. Inference
uses no Python/PHP provider, parser, source execution or dependency resolution.
Existing models, raw source, licenses, split assignments and experiments remain.
