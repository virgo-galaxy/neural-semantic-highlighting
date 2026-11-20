# Model versions, caching and failures

Both local and remote delivery use the selected ONNX and metadata hashes. The
browser checks bytes loaded from persistent storage as well as bytes downloaded
from the resource host. A new revision has a different key. Corrupted cache
entries are deleted and downloaded again; invalid network bytes are rejected.

The default policy is shared by both modes:

```ts
const highlighter = createHighlighter({
  modelBaseUrl: "https://storage.example.com/highlighting/",
  cache: { persistent: true, maxBytes: 64_000_000 },
  maxLoadedModels: 4,
  downloadTimeoutMs: 30_000,
});
```

- Persistent storage uses an origin-scoped CacheStorage namespace and a
  best-effort 64 MB budget, evicting least-recently-used resources. Keys contain
  only content hashes. Source code and signed URLs are never stored there.
- CacheStorage may be unavailable, quota-limited or cleared by the browser. The
  highlighter then downloads verified bytes normally. `persistent: false`
  explicitly disables this cache; ordinary browser HTTP caching remains separate.
- Each Worker retains at most four idle/loaded ONNX inference sessions by default.
  Least-recently-used idle sessions are released. Active requests are protected;
  the limit is reapplied after active work completes. Releasing a session does
  not delete its verified persistent bytes. Failed sessions are discarded.
- Downloads and asynchronous URL resolution time out after 30 seconds. The
  highlighter does not silently retry indefinitely. Call `highlight` again to
  retry; failed metadata and model URL promises do not poison later attempts.

Public/static resources already in persistent storage can be reused after a
reload without reaching their resource host. A private URL callback may still
need its application signing service for model URL resolution on a new instance.
CacheStorage is shared by the application's origin, not across different sites.
See the [Cache API documentation](https://developer.mozilla.org/en-US/docs/Web/API/Cache)
for browser-managed storage limits and eviction.

## Clear downloaded models

```ts
import { clearModelCache } from "@nsh/highlighter";

highlighter.close(); // Release this instance's sessions and pending work.
await clearModelCache(); // Only this library's persistent model cache.
// Create a new highlighter when needed.
```

`clearModelCache()` returns whether a cache was removed; unavailable/empty storage
returns false. It does not change the Dataset, selected weights, browser HTTP
cache or another application's storage. Other active highlighter instances keep
their already loaded sessions until closed or evicted.

## Handle loading errors

```ts
import { ModelAssetError } from "@nsh/highlighter";

try {
  const result = await highlighter.highlight(source, { language: "tsx" });
  // Render result.html.
} catch (error) {
  if (error instanceof ModelAssetError) {
    console.error(error.code, error.modelId, error.kind, error.status);
  }
  // Keep escaped/plain source visible and offer a retry.
}
```

`code` is `network`, `http`, `timeout` or `integrity`. `kind` identifies `model`
or `metadata`; HTTP failures also provide `status`. Worker errors retain these
fields on the main thread. A CORS rejection and a disconnected network cannot
always be distinguished by browser fetch, so their message suggests checking
both. An integrity failure requires the correct exported files at the pinned
paths; retrying unchanged bad files cannot fix it.
