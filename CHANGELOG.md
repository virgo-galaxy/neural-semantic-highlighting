# Changelog

## 0.1.1 - 2026-11-25

- Add `highlighter.observeElement()` for opt-in, one-time highlighting of existing code blocks as they enter the viewport or a custom scroll container.
- Support `rootMargin` to start highlighting before the block becomes visible. The default margin is `0px`.
- Return a cleanup function that stops observation and skips late rendering when a block is removed or reused.

## 0.1.0 - 2026-11-25

- Publish the browser highlighter as `@virgo-nsh/highlighter`, with semantic spans, escaped HTML, themes, and on-demand loading of separately hosted models.
