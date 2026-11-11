# JSON / JSONC independent Golden

48 separately hand-marked cases: 20 paired JSON/JSONC cases plus eight JSONC-specific
comment/trailing-comma cases. They cover keys versus equal string values, nested
containers, signed/exponent/large numbers, keywords, escaped quotes/backslashes,
Unicode/CRLF, duplicate/prototype-looking names and opaque string contents.
Expectations are independent of parser output. Focused tests reject JSON5 syntax,
strict-JSON comments/trailing commas and fault-tolerant recovery of invalid input.
Golden and display sources are outside training. Teacher agreement, strict neural
Golden agreement and natural held-out scores remain separate evidence.
