import { highlight } from "./engine.js";
import type { ModelRequest } from "./types.js";

const scope = self as unknown as DedicatedWorkerGlobalScope;
let queue = Promise.resolve();
scope.addEventListener(
  "message",
  (event: MessageEvent<{ id: number; model: ModelRequest; source: string }>) => {
    const { id, model, source } = event.data;
    queue = queue.then(async () => {
      try {
        scope.postMessage({ id, result: await highlight(model, source) });
      } catch (error) {
        scope.postMessage({ id, error: error instanceof Error ? error.message : String(error) });
      }
    });
  },
);
