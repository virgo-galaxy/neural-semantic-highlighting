# Vue data

Use `make dataset-vue` for capture, offline Gold, validation and immutable grouped
byte preparation. Source, Gold and prepared tensors remain outside Git under
`NSH_DATASET_ROOT/vue` (default `~/Datasets/neural-semantic-highlighting/vue`).
The collector freezes original UTF-8 bytes, profile and source-group provenance;
dependencies, generated files, fixtures and NSH demonstrations are excluded.

`git-sources.json` pins only official Vuex 3 / Vuex 4 / Pinia 2 component selections.
Fetch only `.vue` and root licenses, verifying Git blob IDs and SHA-256 locks.
Source profiles are explicit: Vue 2, Vue 3 and the Vue 3.2-era Pinia release. They
are not inferred from model output. Existing Vite/TanStack components supplement
those sources. No import, script, preprocessor or component is executed.

`generate_curriculum.py` writes a small, original immutable curriculum by version
profile and template family. It never reads Golden or Playground source. Source
locks bind generator code and every file. Prior versions remain preserved. Focus
presentations are separately counted and cannot replace real-source validation.

Related version siblings (Vuex example families, TanStack basic 2.6/2.7/3 examples)
are explicitly assigned a common source-directory family before splitting. Exact
copies merge; unrelated cross-group lexical/shape copies remain excluded. This
keeps a versioned near-copy from leaking across train/validation/test without
discarding all older-version source. Other directories and curriculum families
remain intact. Every profile/stream must retain three independent source groups;
preparation fails if this requirement disappears after deduplication.

Offline `vue-eslint-parser` locations preserve original source and support both
template dialects. Its HTML-only self-closing-element warning is ignored because
SFC templates support self-closing components/elements; all other parse errors
remain failures. Gold failures retain source and reasons in quarantine. The
dependency lock, labeler, schema, semantic contract, grouping and byte-builder
hashes bind each snapshot. Evaluation windows never use Gold cuts.

`split-groups.json` freezes the source-family assignments of the first trained
snapshot. Later curriculum/source revisions restore every overlapping family's
original split; new groups are allocated without moving the old holdouts. The
map hash is part of preparation identity. Preserve this map when adding samples,
so a previously inspected validation document cannot become a new test example.

Composed reference Gold reuses the existing script teacher, adds only missing
punctuation leaves identified by the official TypeScript AST, and respects
intentional neutral JSX text. It does not invent roles for arbitrary uncovered
identifiers. This offline adapter never changes child-model runtime predictions.
