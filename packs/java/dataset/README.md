# Java dataset

Original bytes, source/license locks, Gold and prepared snapshots stay outside Git
under `~/Datasets/neural-semantic-highlighting/java`. Sources are pinned Apache
Commons Lang, Gson and Spring Guide files plus a bounded local OpenJDK 22.0.1
source capture. Full upstream licenses are retained. Original focused tasks live
in their own source families; Golden and Playground are never collection roots.

`make dataset-java` captures sources, generates tasks, collects, labels, validates
and prepares. The offline JDK teacher parses with annotation processing disabled;
it never analyzes imported code, executes Java or invokes a project build. Lexical,
parse, source-range and Unicode failures are quarantined. See `SEMANTICS.md` for the
bounded source-local roles and supported syntax.

Prepared data excludes exact, lexical and normalized copies across families, then
allocates complete families before byte windows. The first assignments must be
frozen in `split-groups.json` before training. Later revisions retain them. Required
modern features must be represented by multiple training families. Natural source,
focused tasks, Golden and displayed probes are separate evidence.

Full training checkpoints stay under `artifacts/java`, not the selected inference
bundle. The repository, original private task curriculum and dataset stay private;
these commands do not publish upstream sources or install another Java runtime.
