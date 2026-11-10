# PHP

Standalone PHP base highlighting for `.php`, `.phtml` and tagless snippets.
Covers modern PHP functions, classes/interfaces/traits/enums, variables/properties,
arrays, closures, attributes, nullsafe/match syntax, interpolation and heredoc/nowdoc.
PHP/HTML templates reuse the existing HTML (and JS/CSS) models inside regions
predicted by the PHP model. No PHP execution, Composer or runtime parsing occurs.

Use `language: "php"`. The [semantic contract](SEMANTICS.md) distinguishes base
PHP/region evidence from composed HTML quality. See [dataset](dataset/README.md)
and [training](../../training/php/README.md) for the established offline workflow.
No PHP interpreter, SDK, server or new global environment is installed/required.
