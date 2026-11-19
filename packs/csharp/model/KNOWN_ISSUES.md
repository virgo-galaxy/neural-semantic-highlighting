# csharp measured limits

- Finite-context names, nested/long content and source-local semantic roles remain approximate.
- Exact-span F1 is a bounded corpus measure, not a guarantee for all files. Individual dialects, cohorts, rare roles and strict Golden outcomes remain separate.
- Neural windows use original bytes and UTF-16 output offsets; no input execution, language SDK, parser or spelling-based repair is used at runtime.
- Selected overlapping windows improve edge robustness but cost additional inference on long documents. Short snippets retain the single-window path.
