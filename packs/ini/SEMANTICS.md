# INI source-local semantic contract

One `ini` profile covers common INI and explicitly selected INI-style configuration,
including .ini/.cfg and EditorConfig source. Extensions do not guarantee an
application's dialect. The independent existing CPython ConfigParser validates
structure; the pack-owned scanner retains every original source range. No new
SDK, external dependency or parser download is needed.

Section brackets use separate punctuation; the complete original inner section
name uses namespace, including dots, quotes, spaces and nested glob brackets.
Option names are properties, preserving case, spaces, literal quote characters,
array-looking [] suffixes and duplicates. The first = or : separates an option;
that one delimiter uses punctuation. Root options, repeated sections/options,
valueless options, empty values, indented sections and defaults-looking names
are supported without merging the highlighted physical source.

Whole-line # and ; comments (optionally indented) use comment, excluding line
endings. Header suffixes may contain such a comment. Inline #/; within an option
value are literal data, consistent with ConfigParser's default no-inline-comment
mode. This avoids cutting URLs, fragments, semicolon lists and quoted text. Other
application-specific inline comment/escape rules are outside this profile.

Each nonempty original value line uses one whole range, excluding surrounding
ASCII spaces/tabs. Whole unquoted true/false/yes/no/on/off (case insensitive) use
keyword. Whole decimal/scientific/signed/hex numeric spellings use number. All
other values use string, including quoted numbers/booleans, units, dates, null,
regex, JSON-looking values, URLs and expressions. These are display conventions,
not INI type coercion; ConfigParser stores string values. No escape decoding,
interpolation, command execution or nested language parsing occurs.

Lines indented deeper than the preceding option are continuation strings, even
when they resemble assignments, booleans or headers. Each physical continuation
line keeps a separate string range. Full-line comments retain comment roles;
blank lines keep the continuation context but create no tokens. A continued
valueless option fails closed. Empty/comment-only editor input is supported.
BOM uses punctuation and remains in the original output; CRLF/Unicode retain
original UTF-16 offsets. Bare CR and unsupported control/line-separator forms,
invalid/empty section headers, empty keys, malformed header suffixes, parser
errors, structure disagreement, overlaps and coverage gaps fail closed.

Validation disables interpolation, preserves key case and permits duplicates.
A unique synthetic root exists only in validation, allowing root options in the
existing Python 3.12 parser; no source text or offsets are rewritten. DEFAULT is
an ordinary highlighted section. The independently parsed section/key inventory
must agree with scanner structure; parser values are never expanded or loaded
as application settings. Python, ConfigParser and teacher hashes are retained.
See [ConfigParser reference](https://docs.python.org/3.12/library/configparser.html).

The browser/Playground uses selected float32 neural ONNX weights in the existing
Worker. No parser, source regular expression, environment/configuration loader
or spelling repair runs during inference. Context remains 512 original UTF-8
bytes. Section/key/value roles, quote and continuation boundaries are approximate.
.env, general .conf syntax and full application dialect validation are separate
work; explicitly pass INI for known INI-format .conf content. Generic .conf files
are not automatically assigned INI.
