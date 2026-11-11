# Ruby source-local semantic contract

One `ruby` model covers common accepted `.rb`, `.rake`, `.gemspec`, Gemfile and
Rakefile syntax. Gold uses tree-sitter-ruby 0.23.1 at a fixed reviewed revision,
with Tree-sitter 0.25.10 compiled by existing Clang only in project cache. No Ruby
SDK/interpreter, gem installation, project code, Rails application or dependency
executes. Browser/native inference is neural without parser or source repair.

Classes are types and modules are namespaces. Constant CST nodes remain constants
unless a local class/module binding gives a type/namespace role. No capitalization
or external dependency heuristic resolves classes. Top-level method definitions
use function roles; class/module/singleton definitions and receiver calls are
methods. Constructor `new`/`initialize` calls retain syntactic method roles.
Instance/class variables are properties, globals are variables, assigned locals
are variables, and constant assignments have constant declaration roles.

Parameter/default/keyword/splat/block parameters are parameters. Blocks/lambdas
capture enclosing locals and can shadow with parameters/block-local variables.
Method and class/module boundaries hide outer local variables while retaining
source-local constant/type and method approximations. Unresolved bare identifiers
are syntactic calls (function or member method by context), reflecting Ruby's
ambiguous bare-call syntax without executing code. Numbered `_1`–`_9` and common
implicit `it` are parameter approximations in eligible parameterless blocks;
known assigned `it` remains a local. Dynamic dispatch, metaprogramming, Rails DSLs,
refinements, reopenings and imported APIs are not resolved.

Hash keys are properties; call keyword labels are parameters. Pattern bindings,
including shorthand hash patterns, bind local names without rescanning. Symbols
are constants; percent symbol/string arrays retain string-literal syntax. Numeric,
rational and complex literals are numbers. Strings, characters, regex, percent
literals, subshell syntax and heredocs remain string fragments, with interpolation
expressions retaining code roles and `#{`/`}` punctuation. No subshell/heredoc or
interpolated code executes and no embedded-language model is inferred from names.

CST ranges supply all literal fragments and heredoc headers/bodies/terminators.
Matching nonempty heredoc-end nodes are required because the grammar may accept
an unfinished heredoc at EOF; empty delimiters or terminators not recognized at
EOF fail closed. Original CRLF and Unicode remain unchanged, with UTF-16 offsets.
Leading BOM is punctuation when accepted by the grammar. Explicit backslash-LF
or backslash-CRLF extras omitted by CST children are punctuation in original
nonliteral gaps; all other nonspace gaps still fail closed. Literal content is
never scanned by this bounded offline adapter. Unknown tokens, parse
errors, overlap, Unicode and nonspace coverage gaps are rejected. Grammar
acceptance does not certify every Ruby release, compiler semantic or package API.
