# C++

Standalone C++ source-local semantic highlighting for source and explicit C++
headers. Covers classes, constructors/destructors, methods, fields, templates,
namespaces, aliases/enums, lambdas, pointers/references, standard-library shapes,
concepts/requires, macros, directives and original literals/comments.

Use `language: "cpp"` (`c++` and `cxx` aliases). `.h` filename routing remains C;
explicit C++ header text can always use `cpp`. No compiler/SDK/parser is required
by inference. C remains a separate pack and its selected weights stay unchanged.

See [the semantic contract](SEMANTICS.md), [dataset workflow](dataset/README.md)
and [training workflow](../../training/cpp/README.md) for scope and reproducibility.
