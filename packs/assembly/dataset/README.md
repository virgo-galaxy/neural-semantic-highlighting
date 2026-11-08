# Assembly corpus

Bounded original source captures select 16 NASM routines from FFmpeg 7.1.1,
16 MASM routines from .NET runtime 10.0 and 20 x86-64 / 13 AArch64 assembly files
from musl 1.2.5. Git revisions/blobs or official archive/member SHA-256 values are
pinned in `upstreams.json`. Complete original licenses remain next to the source;
Git sources also retain a complete combined license bundle for collector lineage.
No repository is cloned in full. No source, build, assembler, emulator or executable
is installed or run. Include paths and macros are not followed or expanded.

Related routine/template siblings stay together; musl cross-architecture versions
share source family IDs. Original short arithmetic, memory, branch, stack, vector,
macro, directive, string and preprocessor tasks share task IDs across syntax
profiles. Source position, names, constants and CRLF vary within the same family.
Golden and Playground are never collected. Freeze the first prepared family map
before training, retain all future assignments and keep natural/focus scores apart.

Primary syntax references:

- [NASM language](https://www.nasm.us/doc/nasm03.html)
- [GNU assembler manual](https://sourceware.org/binutils/docs/as.html)
- [MASM directives](https://learn.microsoft.com/en-us/cpp/assembler/masm/directives-reference)

The offline display grammar deliberately has bounded semantics; it is not an
assembler acceptance test or a guarantee for every ISA/dialect/version.

The selected original revision is `curriculum-v2`: MASM END directives stay after
conditional/data blocks. The first source/Gold/prepared revision remains preserved;
related family IDs are unchanged. No native assembler is needed for these checks.
