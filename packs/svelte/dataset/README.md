# Svelte dataset

External root: `~/Datasets/neural-semantic-highlighting/svelte`.

`upstreams.json` pins 64 library components each from Bits UI (legacy syntax),
LayerChart and Flowbite Svelte (modern syntax), with Git blobs and complete
licenses. `fetch_sources.py` reads those exact files without builds or execution.
`generate_curriculum.py` adds original component tasks; variants stay in intact
families. Golden and Playground sources are excluded from collection.

The official Svelte 5.38.0 compiler bundle is cached under ignored
`artifacts/tools/svelte-gold`; archive integrity, original files, Node, entity
library, teacher and config are bound into Gold provenance. No npm/global tool
installation, component execution or external preprocessor is required.

`make dataset-svelte` captures sources, labels original UTF-16 coordinates,
validates full coverage and prepares immutable byte snapshots. Natural and focus
streams stay separate. Exact/lexical/normalized cross-family copies are excluded;
source-family assignments in `split-groups.json` are frozen before training.
Malformed/unmapped sources are quarantined with their original identities.
