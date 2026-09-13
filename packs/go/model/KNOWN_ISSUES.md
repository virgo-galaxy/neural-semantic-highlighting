# Known issues

These are observed limits of the selected Go model, not evidence that the Go runtime uses a parser
or scanner. Runtime inference remains neural-only.

## Function-range method ambiguity

On the held-out focused test, `function-range / method` scored `0.8571` (support 64). The model
recalled 48 of 64 method spans with no method false positives; the missing method spans appeared as
selector-role confusion. Ordinary natural Go test data was substantially stronger (`method` F1
about `0.9752`).

This is worth revisiting only if real Playground/product code shows a recurring visible problem.
Do not extend training solely to force this synthetic lane above an arbitrary threshold.

## Strings longer than the model context

The model context is 512 UTF-8 bytes. A raw string may itself exceed that context, so a later window
can begin inside a string without seeing its opening backtick. That case is intrinsically
underdetermined for a stateless 512-byte neural window.

The focused `strings / string` stress lane therefore remains a diagnostic rather than a hard
checkpoint-selection gate. Natural held-out Go data still measures ordinary `string` quality and
scored about `0.9630` F1 in the selected model's test report.

## Cross-file information

The model receives source text, not a project-wide symbol table. A declaration in another file or
outside the current 512-byte context may be unavailable when classifying a selector or identifier.
Such cases are architecture/context limits rather than automatic reasons to keep training.

## Acceptance rule

Model changes should be driven by reproducible, product-visible errors where the necessary evidence
is present in the input context. Aggregate score chasing and impossible cross-context cases are not
release blockers by themselves.
