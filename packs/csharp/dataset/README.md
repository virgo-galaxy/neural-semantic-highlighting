# C# dataset

Original source bytes, full licenses, Gold and prepared snapshots stay external
under `~/Datasets/neural-semantic-highlighting/csharp`. Bounded captures are pinned
.NET runtime 9.0, Newtonsoft.Json 13.0.3 and Dapper 2.1.66 sources. Downloading these
files does not install .NET or build/run their projects. Source revision/blob hashes
and complete original licenses remain with the external capture.

`make dataset-csharp-tools` downloads fixed official parser/runtime source files
and builds only that offline parser into ignored `artifacts/tools/csharp-gold`,
using the already installed native compiler. There is no global install and no
pip/npm environment change. The parser and source-local teacher never execute C#.
`make dataset-csharp` then collects, labels, validates and prepares the pack data.

Original mixed syntax tasks stay in their family before windows. Golden and
Playground are excluded. Parse errors, missing syntax, uncovered source and invalid
Unicode coordinates are quarantined, not completed with a fallback lexer. The
pinned grammar is not a full Roslyn/project semantic resolver and does not certify
every later/preview language version. See the semantic contract for scope.

Prepare performs exact, lexical and identifier-normalized copy auditing, then
allocates intact source/task families. Freeze the first family map in
`split-groups.json` before training and preserve it for later revisions. Natural,
focused and visible probes are separate evidence. Full training runs live in
`artifacts/csharp`; selected inference exports are not resumable checkpoints.
