# Assembly semantic contract

One Assembly entry covers common NASM/Intel x86, GNU x86 AT&T (with focused Intel
mode), MASM x86/x64 and GNU-style AArch64 source. The initial real-source profiles
are `nasm`, `gas`, `masm`, `aarch64`. These are offline coverage annotations, not
runtime architecture selectors. `.asm`/`.s`/`.S`/`.nasm`/`.masm` and assembly `.inc`
all share the same document kind. No assembler, simulator, emulator, native Windows
host, x86 runtime, module loader or source execution is required or invoked.

Offline Gold uses pinned isolated lexer machinery and one shared source-local
grammar; common source has common labels across profiles. Instruction/macro-call
positions, assembler directives and preprocessor words use keyword. Registers
use variable plus default-library; ordinary symbols use variable. Named/numeric
labels, PROC entries, visible macros and common cglobal/LEAF_ENTRY-style helpers
use function declarations; visible label and branch/call references use function.
Data bindings/EQU/DEFINE use variable declarations. Size words use type in operands.
Macro positional and backslash parameters use parameter; macro-local symbols
remain variable-like. These are display roles, not ISA validation, function/data
symbol resolution, macro expansion or linker/scope analysis.

Strings are opaque whole quoted regions; include paths are never followed.
Numbers, arithmetic, relocation spelling and structural punctuation preserve
original tokens. Comments use semicolon, //, /* */ and GNU hash spelling. Hash is
an AArch64 immediate operator when visible register/instruction context supports
it; ordinary GNU hash comments remain comments. This bounded offline ambiguity
rule is profile-independent. Semicolon-separated GNU instructions, MASM COMMENT
blocks, exotic macro dialects and other CPU architectures are outside this first
baseline's certified scope. Source fragments need not form executable programs.

Original UTF-8, CRLF, Unicode and tabs remain unchanged; public spans use original
UTF-16 offsets with full non-whitespace coverage and no overlap. Touching predicted
comment ranges may coalesce and modifier roles are masked by predicted types;
these decoder rules never inspect source text, spelling or Gold boundaries.
The neural runtime imports no offline lexer and does not apply grammar repair.

Related task variants share family IDs across profiles. Upstream routine/template
siblings and cross-architecture implementations are grouped before windows;
exact/lexical/normalized copies are audited. Frozen source families, Golden,
short resumable training, validation-based selection and a first independent
adaptive test follow the same workflow as previous packs. Natural/focus/profile
metrics remain separate. Context remains 512 UTF-8 bytes; preserve all old models,
source data, full checkpoints and experiments. Repository remains private.
