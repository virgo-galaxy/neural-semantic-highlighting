import type { HighlightResult, SemanticPack } from "@nsh/core";

import {
  type BrowserRuntimeOptions,
  ModelAssetError,
  type ModelAssetFailure,
  runtimePolicy,
} from "./assets.js";
import type { BrowserModel } from "./types.js";
export type {
  BrowserRuntimeOptions,
  ModelAssetFailure,
  ModelCacheOptions,
  RuntimePolicy,
} from "./assets.js";
export { clearModelCache, ModelAssetCache, ModelAssetError, runtimePolicy } from "./assets.js";
export type { BrowserModel } from "./types.js";

interface Pending {
  resolve(result: HighlightResult): void;
  reject(error: Error): void;
  modelKey: string;
}

/** One reusable worker; models load lazily and source never leaves the browser. */
export class BrowserRuntime {
  #worker: Worker | undefined;
  #closed = false;
  #id = 0;
  readonly #pending = new Map<number, Pending>();
  readonly #modelUrls = new Map<string, string | Promise<string>>();
  readonly #policy;

  constructor(options: BrowserRuntimeOptions = {}) {
    this.#policy = runtimePolicy(options);
  }

  createPack(model: BrowserModel): SemanticPack {
    return {
      manifest: model.manifest,
      highlight: async ({ source, documentKind }) => {
        if (!model.manifest.documentKinds.some((kind) => kind.id === documentKind))
          throw new Error(`Unsupported document kind: ${documentKind}`);
        if (this.#closed) throw new Error("Browser highlighter is closed");
        if (typeof source !== "string") throw new Error("Source must be a string");
        if (!source.length) return { offsetEncoding: "utf-16", spans: [] };
        const id = ++this.#id;
        const { modelUrl, dependencies: _dependencies, ...metadata } = model;
        void _dependencies;
        const modelKey = model.id + ":" + model.sha256;
        return new Promise<HighlightResult>((resolve, reject) => {
          this.#pending.set(id, { resolve, reject, modelKey });
          const fail = (error: unknown) => {
            this.#pending.delete(id);
            reject(error);
          };
          const send = (url: string) => {
            if (!this.#pending.has(id)) return;
            try {
              const worker = this.#ensureWorker();
              worker.postMessage({
                id,
                source,
                model: { ...metadata, modelUrl: url },
                runtime: this.#policy,
              });
            } catch (error) {
              fail(error);
            }
          };
          try {
            let url = this.#modelUrls.get(modelKey);
            if (url === undefined) {
              const value = modelUrl();
              if (typeof value === "string") {
                url = value;
              } else {
                const pending: Promise<string> = Promise.resolve(value)
                  .then((resolved) => {
                    if (typeof resolved !== "string") throw new Error("Invalid model URL");
                    if (this.#modelUrls.get(modelKey) === pending)
                      this.#modelUrls.set(modelKey, resolved);
                    return resolved;
                  })
                  .catch((error: unknown) => {
                    if (this.#modelUrls.get(modelKey) === pending) this.#modelUrls.delete(modelKey);
                    throw error;
                  });
                url = pending;
              }
              this.#modelUrls.set(modelKey, url);
            }
            if (typeof url === "string") send(url);
            else void url.then(send, fail);
          } catch (error) {
            fail(error);
          }
        });
      },
    };
  }

  #ensureWorker(): Worker {
    if (this.#worker) return this.#worker;
    if (typeof Worker === "undefined")
      throw new Error("Browser inference requires a Web Worker; call highlighting on the client");
    const worker = new Worker(new URL("./worker.js", import.meta.url), {
      type: "module",
      name: "NSH inference",
    });
    worker.addEventListener(
      "message",
      (
        event: MessageEvent<{
          id: number;
          result?: HighlightResult;
          error?: string | ModelAssetFailure;
        }>,
      ) => {
        const response = event.data;
        const pending = this.#pending.get(response.id);
        if (!pending) return;
        this.#pending.delete(response.id);
        if (response.error) {
          this.#modelUrls.delete(pending.modelKey);
          pending.reject(
            typeof response.error === "string"
              ? new Error(response.error)
              : new ModelAssetError(
                  response.error.code,
                  response.error.modelId,
                  response.error.kind,
                  response.error.status,
                ),
          );
        } else if (response.result) pending.resolve(response.result);
        else pending.reject(new Error("Browser worker returned no result"));
      },
    );
    worker.addEventListener("error", (event) => {
      this.#fail(new Error(event.message || "Browser inference worker failed"));
      worker.terminate();
      this.#worker = undefined;
    });
    this.#worker = worker;
    return worker;
  }

  #fail(error: Error) {
    for (const pending of this.#pending.values()) pending.reject(error);
    this.#pending.clear();
    this.#modelUrls.clear();
  }

  close(): void {
    this.#closed = true;
    this.#worker?.terminate();
    this.#worker = undefined;
    this.#fail(new Error("Browser highlighter was closed"));
  }
}
