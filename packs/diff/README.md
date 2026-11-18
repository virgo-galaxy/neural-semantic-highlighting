# Diff / Patch pack

One standalone neural model highlights common unified and Git patches. `.diff`
and `.patch` share weights: additions/deletions, original context, file/hunk
headers, mode/rename/copy metadata, no-newline markers and mail patch text.
Changed code is opaque Diff content. Browser inference requires no Git, SDK,
Python, source parser or patch application.

See [semantics](SEMANTICS.md), [dataset](dataset/README.md),
[Golden](fixtures/README.md), [training](../../training/diff/README.md)
and the root [consumer guide](../../README.md).
