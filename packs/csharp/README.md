# C#

One C# source entry (`csharp`, `.cs`) with the existing local/browser neural
highlighter protocol. Common class/record/struct/interface/enum, property/event,
generic, attribute, async, Lambda, LINQ, pattern and modern string syntax share
one model. Different .NET SDK versions do not create separate runtime models.

The offline teacher uses pinned parse-only grammar sources built into project
cache with existing native tools. No .NET SDK, Mono, CLR or global parser package
is installed. No collected C# source or project is compiled, loaded or executed.

Read [SEMANTICS.md](SEMANTICS.md) for bounded syntax/source-local roles and
[training](../../training/csharp/README.md) for the established data, checkpoint,
short-experiment and matching-test export workflow. Final inference uses original
text and learned weights; no offline parser or SDK is needed by frontend consumers.
