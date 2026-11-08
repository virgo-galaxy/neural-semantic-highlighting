# Shell semantic contract

One `bash` document kind and one Shell UI entry cover POSIX sh, Bash, Zsh and
Csh/Tcsh source. The four profiles are offline coverage/evaluation annotations,
not separate runtime models or a promise that those shells execute each other's
programs. Git Bash uses Bash syntax; its Windows environment is not a new language.

The offline teacher uses pinned Pygments 2.21.0 Bash/Tcsh tokenization and an
explicit local command-position adapter. It is a lexical/syntactic display
contract, not a compiler, command execution engine or complete shell interpreter.
Source is never executed, sourced, expanded, imported or sent to a shell service.
Neural runtime imports neither this teacher nor Pygments and performs no source
regex repair, dialect sniffing, command lookup or filename-dependent role changes.

| Source                                                          | Role                                                       |
| --------------------------------------------------------------- | ---------------------------------------------------------- |
| Shell reserved/control words                                    | `keyword`                                                  |
| Comments and shebang                                            | `comment`; trailing physical newline stays outside         |
| Quoted fragments, heredoc bodies, ordinary bare arguments/paths | `string`                                                   |
| Numeric literals                                                | `number`                                                   |
| Expansion, arithmetic, redirection and control operators        | `operator`                                                 |
| Structural braces/parentheses, separators                       | `punctuation`                                              |
| Direct command/function names                                   | `function`; visible function definitions add `declaration` |
| Variables, positional/special parameters                        | `variable`; visible assignments/bindings add `declaration` |
| Bare option flags                                               | `parameter`                                                |

Recognized builtin commands get `default-library` only in command position and
when not shadowed by a visible function declaration. Literal command arguments
that happen to spell a builtin keep argument roles. Command positions reset at
newlines, pipelines, list separators and visible control/body boundaries.
Unknown direct commands are functions; expansion-based commands remain variables
or strings. No executable lookup, alias expansion or external command resolution
is attempted. Adjacent lexer fragments of a string are canonicalized into one
span; separated literals remain separate. Interpolated variable/command tokens
retain their own roles where provided by the lexer.

Ranges use original Unicode characters mapped to UTF-16 `[start,end)` offsets,
with complete non-whitespace Gold coverage. No newline normalization, tab
expansion or automatic EOF newline is allowed. Unknown lexer tokens and invalid
ranges are quarantined rather than filled with guesses. Lexical acceptance does
not certify that the program executes or that every shell version accepts it.

Independent Golden/Playground stay outside collection. Original source families,
related versions and normalized copies are separated before windows; frozen
family assignments persist across revisions. Natural and focused scores are
reported per profile, including coverage gaps. Rare dialect constructs, deeply
nested expansion and objects beyond the 512-byte model context remain measured
limits. Shell session transcripts and foreign-language programs embedded in
arguments/heredocs are not separately parsed or executed.
