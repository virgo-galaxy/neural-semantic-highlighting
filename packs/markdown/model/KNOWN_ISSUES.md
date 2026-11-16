# Markdown known issues

- First new independent real-source exact-span F1 is **95.10%**
  on 20 files; role macro F1 is 93.80%. This bounded
  family holdout does not certify every Markdown extension or ecosystem.
- Fenced bodies remain the weaker role: fresh embedded-code exact-span F1 is
  **78.57%** (25 reference bodies); legacy body F1 is
  83.72%. Visible 7/7 complete body/info
  ranges, including Python imports and unknown-language prose, do not guarantee
  every long or nested fence. Composition uses predicted regions only.
- Fresh prose F1 is 93.18%; heading F1 is
  96.42%. HTML/frontmatter strings, entities,
  inline code, URL/title boundaries and nested formatting can still be wrong.
  The context remains 512 bytes, so distant/long content can lose context.
- Strict edge probes remain **21/48** exact including modifiers, with
  74.48% base-span F1.
  Visible Unicode/frontmatter `unicode.md` is 78.05%; `formatting.md` is 90.91%.
  These limitations are retained separately from the much stronger real test.
- Container/indented code, raw HTML and frontmatter remain opaque. Explicit
  registered language info routes top-level fences; unknown/unregistered and
  recursive Markdown bodies remain code when predicted. No MDX, math/template
  processing, content-based language detection, Markdown rendering or execution
  is claimed. Runtime uses no parser, regex or source-spelling repair.
- Browser and Python share the same optional structured decoder. Other packs
  retain their greedy decoder. Numerical and document parity establish
  consistency and source-text preservation, not perfect semantic accuracy.
