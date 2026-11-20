import { type BrowserRuntimeOptions, ModelAssetError } from "./assets.js";
import { highlight } from "./engine.js";
import type { ModelRequest } from "./types.js";

const scope = self as unknown as DedicatedWorkerGlobalScope;
let queue = Promise.resolve();
scope.addEventListener(
  "message",
  (
    event: MessageEvent<{
      id: number;
      model: ModelRequest;
      source: string;
      runtime?: BrowserRuntimeOptions;
    }>,
  ) => {
    const { id, model, source, runtime } = event.data;
    queue = queue.then(async () => {
      try {
        scope.postMessage({ id, result: await highlight(model, source, runtime) });
      } catch (error) {
        scope.postMessage({
          id,
          error:
            error instanceof ModelAssetError
              ? error.toJSON()
              : error instanceof Error
                ? error.message
                : String(error),
        });
      }
    });
  },
);
