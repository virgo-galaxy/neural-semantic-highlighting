# Shell corpus

The bounded source capture retains 88 real upstream programs/functions/configs
from GNU Bash 5.3, Zsh 5.9 and Tcsh 6.24.16. Only selected text source and license
files are stored; no shell is compiled, installed, sourced or executed. Upstream
URLs/revisions, archive hashes, original file bytes and copyright/license text
remain frozen externally. `fetch_sources.py` refuses changed existing revisions.

The original curriculum adds 768 small programs across POSIX/Bash/Zsh/Csh. A
grammar family stays in the same group across related profiles, with distinct
original source headers. This prevents shared grammar templates leaking between
train/validation/test. Related Bash function revisions and Csh startup/login
configs are also grouped before windows. Golden/Playground are never sources.

Pinned Pygments 2.21.0 is extracted into ignored `artifacts/tools` as an offline
tool, without pip installation or system environment changes. Its full file
hashes and BSD license remain alongside the tool. The teacher uses unprocessed
original-coordinate tokens and a bounded command/expansion-position adapter;
it is not an execution validator or complete shell parser.

`sources.json` declares profiles and family aliases. `split-groups.json` freezes
assignments before the first training pass. Original source, Gold and prepared
binary windows stay under `~/Datasets/neural-semantic-highlighting/bash`, while
full checkpoints/logs stay under `artifacts/bash`. Preserve all old snapshots.

```sh
make dataset-bash
make test-labeling-bash
make train-bash-smoke BASH_DEVICE=mps
```

Natural coverage is small and uneven, especially Csh: its large completion
program stays intact rather than splitting snippets across holdouts. Per-profile
natural/focus reports must remain separate and must not imply broad project or
version coverage from those few files. Valid ranges/complete Gold coverage do
not prove the code runs under every shell version.

Later original revisions add 1,024 short-position fragments within the existing
frozen grammar families and 576 mixed-feature programs in independent task
families. Existing holdouts never move into training. Mixed tasks combine loops,
conditionals, commands and data so holding out a task does not hold out an entire
common syntax. Preparation requires loops and conditionals in at least three
independent training families for every coverage profile, before any training run.

Loop-entry fragments retain their parent task's group and add source-position-zero
control examples. Independent collection tasks add actual Bash/Zsh/Csh arrays,
with POSIX positional-parameter counterparts. Coverage checks require leading
loops for all profiles and arrays for Bash/Zsh/Csh in three training families.
Documents retain profile identity even when shared syntax has identical source;
those aliases remain in one family and are not additional independent programs.

The bounded Here Document follow-up adds 576 original mixed tasks in
`sources/heredoc-programs-v2`, with ordinary/single-quoted/double-quoted delimiters,
tab stripping, body text resembling shell/HTML/SQL, and commands after the
terminator. Six task families train, one validates and one tests, shared across
POSIX/Bash/Zsh. Both `function name()` and `function name` are included for
Bash/Zsh. An offline exact-line adapter replaces the base lexer's substring
terminator rule; bodies remain whole strings. Independently marked Golden covers
queued documents, CRLF/Unicode, following redirections and arithmetic/here-string
exclusions. Existing sources, snapshots and family assignments are preserved.
