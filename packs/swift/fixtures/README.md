# Independent Swift Golden

28 manually marked source cases cover declarations/references, parameter labels,
generics, properties/methods/initializers, enums, closures, raw/interpolated/regex
strings, nested comments, UTF-16/CRLF, attributes, macros and async/actor syntax.
They are visible development probes, never corpus collection or training roots.
Expected spans are authored independently of the offline teacher.

`make test-labeling-swift` checks all cases plus scope/shadowing, modern syntax,
string-continuation trivia, original Unicode positions, invalid input and the
absence of project execution/capitalization heuristics. Official parsing does not
establish type correctness, framework API availability or macro expansion.
`make challenge-swift SWIFT_CHECKPOINT=...` compares neural output to these same
expectations, keeping full missing/unexpected diagnostics and modifiers.
