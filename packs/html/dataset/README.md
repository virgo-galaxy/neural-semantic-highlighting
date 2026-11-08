# HTML data

Use the existing external corpus first. `sources.json` selects named local roots;
no download or execution is needed. Only `.html`/`.htm` original UTF-8 source is
collected. Dependencies, generated/build outputs, fixture/challenge directories,
empty/minified/oversized files are excluded with preserved source identities.
The NSH Playground source/example directories are not collection roots.

```bash
make dataset-html
```

Storage follows the existing layout under
`~/Datasets/neural-semantic-highlighting/html` (or `NSH_DATASET_ROOT/html`):
`corpora/<hash>`, `gold/<hash>`, `prepared/<hash>`, plus atomic current pointers.
Captured source is immutable. Labeling reads captured bytes rather than a changing
checkout. Failed complete-coverage checks and obsolete-source policy exclusions
remain in quarantine with original source and reasons.

`make dataset-html-sources` fetches the explicitly pinned MDN selections in
`git-sources.json`: HTML examples, Web Components, and only the dialog/popover/
shadow-DOM directories of DOM examples. Only HTML and root license files are
downloaded. Each blob is verified against the pinned Git tree and frozen with
SHA-256 in `source.lock.json`; images, scripts and repository installations are
not downloaded or executed. Existing locked sources are verified and reused.

`make dataset-html-curriculum` generates a small, original grammar curriculum in
an immutable versioned directory with a generator/source hash lock. It is marked
`focus`; collected source remains `natural`. Its templates cover failures seen
in development (attribute forms, entities, raw text, foreign content, script/CSS
strings and typed data) without reading Golden fixture source or answers.
Source/template directories remain intact during splitting, with both streams
balanced separately across holdouts. Real-source and synthetic scores stay
separate; final selection uses real-source validation.

Offline parse5 SAX locations supply original-source boundaries. Entity decoding
identifies reference lengths without replacing the raw source. Scripts/styles
remain explicitly typed opaque regions at this stage. No network requests,
JavaScript execution, imports or preprocessors participate in Gold generation.

Gold identity includes corpus, labeler hash, semantic contract, schema and locked
dependencies. Preparation binds builder hashes, removes exact/cross-group shape
copies, and assigns intact source directories before byte windows. Evaluation
cuts never use Gold boundaries. Keep all prior snapshots and audit exclusions.
