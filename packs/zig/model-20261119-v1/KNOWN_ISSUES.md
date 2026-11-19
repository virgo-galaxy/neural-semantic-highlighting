# Zig known issues

A usable current-source display baseline with a bounded SDK-local contract.

- Only Zig 0.17.1 is targeted. Historical syntax/APIs, master and ZON are outside
  this pack. Highlighting does not certify that arbitrary third-party member
  names, signatures, imports or comptime expressions type-check on this SDK.
- Natural test exact-span F1 is 92.51%
  over 21 files; role macro F1 is
  73.75%. Data comes from one official
  release, with a small, crypto/HTTP-dominated validation holdout. Results do not
  establish universal application-level quality.
- Quoted `@"name"` identifiers can split into builtin/string/name pieces and
  influence nearby roles. Format strings, multiline/long literals and comments
  can split or exchange roles. The mixed string/quoted-identifier display scores
  93.10%. No runtime delimiter scanner or spelling-based repair hides errors.
- Parameters versus variables/properties, inferred type-producing aliases,
  captures, enum versus type names, constants and declaration modifiers remain
  approximate. The teacher uses source-local AST forms and bindings without
  project inference. Uncalled contextual `.empty` shares enum-literal syntax;
  called `.init()` is labeled function by its official call node.
- Neural output is completely exact in 10/23 visible Golden cases.
  The separate teacher passes all 23 marked cases and nine tests;
  teacher exactness is not neural accuracy. Visible examples and inspected
  validation files are development evidence.
- The unchanged 512-byte context limits distant names and long literal/comment
  boundaries. Original text/offset preservation and browser/native parity verify
  consistent predictions, not perfect semantic accuracy.

The host Zig upgrade was explicitly requested. Offline supervision neither
evaluates input comptime code nor follows imports/embed files; no collected
project builds or runs. Browser inference needs no Zig, Python or parser.
Previous model artifacts, data snapshots and full training runs remain preserved.
