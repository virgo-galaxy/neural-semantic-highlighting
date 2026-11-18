# Protocol Buffers known issues

- Independent natural exact-span F1 is 98.55% on 12 files;
  validation is 98.04% on 13. These
  bounded families do not certify every application, proto version or option.
- Names in message/enum/type references, fields versus option properties,
  RPC/oneof roles and declaration/default-library modifiers can still be wrong.
  Per-role counts and F1 are retained in the matching test report.
- Eight authored displays aggregate 99.77%;
  strict Golden is 23/26 whole cases exact including modifiers. Long original
  comments/strings, non-ASCII text, unusual whitespace, nested aggregate options
  and distant structure remain limited by 512-byte context. No runtime parser
  repairs an incorrect boundary. Source text stays complete even if roles miss.
- Offline grammar acceptance does not check edition feature validity, field-number
  constraints, escape semantics, imported names, wire compatibility or complete
  protoc validity. Common proto2/proto3 and grammar-supported edition syntax are
  covered; no guarantee is made for every historical/deprecated or future feature.
- `.proto` definitions are the scope. Binary `.pb`, ProtoJSON, `.textproto` and
  `.pbtxt` data are not extra source kinds. No automatic language detection,
  code generation, environment execution or imported-schema loading is performed.
  Markdown composition still depends on its predicted fence region and registered
  child model. Browser parity is runtime evidence, not an accuracy score.
