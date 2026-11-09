# C

Standalone source-local C semantic highlighting for `.c` and C `.h` files.
The pack covers functions, parameters, typedefs, structs/unions/enums, pointers,
callbacks, local variables, fields, macros, directives, literals and labels.
C++ is a separate language and is not claimed by this pack.

See [the semantic contract](SEMANTICS.md), [dataset workflow](dataset/README.md)
and [training workflow](../../training/c/README.md). Offline grammar/type hints
create supervision only. Selected inference predicts spans from original bytes;
no parser, preprocessor, compiler or source execution is part of inference.
