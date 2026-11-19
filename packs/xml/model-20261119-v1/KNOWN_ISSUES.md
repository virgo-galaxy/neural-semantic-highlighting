# XML / SVG known issues

- Separate natural results: XML **85.87%** on 7 files; SVG **100.00%** on 6 files. SVG's small, bounded sample is not a universal accuracy claim.
- Natural test exact-span F1 is 92.20%
  across 13 files; role macro F1 is
  86.08%. Bounded family holdouts limit
  generalization claims. Grammar acceptance is not full compiler or API validity.
- Natural XML test comment and string exact-span F1 are only 51.28% (15 reference comment spans) and 70.93% (69 string spans), so the aggregate must not hide difficult comment/quoted-content boundaries. The instruction-plus-nested-code CDATA display remains weak (xml/cdata.xml 78.26% exact-span F1): a processing instruction can split into keyword fragments, quoted markup inside CDATA can receive tag/text roles, and escaped closing-tag text can merge entity boundaries. Atom text/whitespace and public-doctype boundaries also remain approximate (feed.xml 97.48%, preferences.plist 97.30%). All eight authored SVG displays reach 100%, which is visible development evidence rather than unseen generalization. Long strings/comments/CDATA and closing modifiers across 512 bytes remain approximate. UTF-8 XML 1.0 is the bounded profile; no XML 1.1, custom entity expansion, DTD/schema validation, SVGZ, SVG path/CSS/JS parsing, template syntax, automatic detection or runtime parser/spelling repair is provided.
- Tag/attribute roles, closing flags, declaration/CDATA boundaries can be wrong. Context is 512 original UTF-8 bytes; long/nested content and Unicode names
  can split boundaries. No parser or spelling-based runtime fix hides these errors.
- The independent teacher passes 48 marked cases and 14
  tests; the neural model is entirely exact in 37/48
  Golden cases. Sixteen displays and ten inspected natural validation files are
  development evidence, separate from the first held-out test. Original-text and
  browser parity checks establish consistency, not semantic perfection.
