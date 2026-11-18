# Protocol Buffers source semantics

A standalone byte model highlights `.proto` definitions: common proto2/proto3
and editions source accepted by the pinned offline grammar, including packages,
imports, message/enum/service definitions, oneof/maps, RPC streaming, reserved
names/ranges, extension declarations and custom/aggregate options. No protoc,
SDK, schema execution, imports, code generation or server is needed at inference.

Original UTF-8 source yields half-open UTF-16 offsets. Keywords, literal strings,
comments, numbers, operators and punctuation have separate roles. Individual
original quoted literals are opaque strings even in concatenated values;
comments between literals remain comments. Contiguous signed numerics are one
number; separated signs remain operators. Comment spans exclude line endings.
BOM is punctuation; qualified names are segmented by punctuation dots.

Message/service names are type declarations; enums and members have distinct
declaration roles. Field names are property declarations, oneof names are label
declarations, RPC names are method declarations, packages are namespace
declarations. Scalar references are type/default-library; user message/enum
references are type without global resolution. Option/aggregate keys are property,
identifier option values are constant. Reserved names are string if quoted and
property if bare. Imported paths and option string bodies are not sub-highlighted.

The offline CST supplies syntax-local labels, not cross-file symbol linking,
field-number validity, edition feature validation or a complete protoc compiler.
No lexical/CST/spelling fallback is used by neural inference. Equal touching
string/comment predictions may coalesce without bridging gaps. Context is 512
bytes; long comments/strings and distant nesting can reduce neural accuracy.
Golden, authored displays, natural validation and independent test stay separate.
