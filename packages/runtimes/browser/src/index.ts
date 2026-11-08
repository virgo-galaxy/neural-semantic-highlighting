import type { HighlightResult, SemanticPack } from "@nsh/core";

import type { BrowserModel } from "./types.js";
export type { BrowserModel } from "./types.js";

interface Pending {
  resolve(result: HighlightResult): void;
  reject(error: Error): void;
}

/** One reusable worker; models load lazily and source never leaves the browser. */
export class BrowserRuntime {
  #worker: Worker | undefined;
  #closed = false;
  #id = 0;
  readonly #pending = new Map<number, Pending>();

  createPack(model: BrowserModel): SemanticPack {
    return {
      manifest: model.manifest,
      highlight: async ({ source, documentKind }) => {
        if (!model.manifest.documentKinds.some((kind) => kind.id === documentKind))
          throw new Error(`Unsupported document kind: ${documentKind}`);
        if (this.#closed) throw new Error("Browser highlighter is closed");
        if (typeof source !== "string") throw new Error("Source must be a string");
        if (!source.length) return { offsetEncoding: "utf-16", spans: [] };
        const worker = this.#ensureWorker();
        const id = ++this.#id;
        const { modelUrl, dependencies: _dependencies, ...metadata } = model;
        void _dependencies;
        const url = modelUrl();
        return new Promise<HighlightResult>((resolve, reject) => {
          this.#pending.set(id, { resolve, reject });
          try {
            worker.postMessage({ id, source, model: { ...metadata, modelUrl: url } });
          } catch (error) {
            this.#pending.delete(id);
            reject(error);
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
      (event: MessageEvent<{ id: number; result?: HighlightResult; error?: string }>) => {
        const response = event.data;
        const pending = this.#pending.get(response.id);
        if (!pending) return;
        this.#pending.delete(response.id);
        if (response.error) pending.reject(new Error(response.error));
        else if (response.result) pending.resolve(response.result);
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
  }

  close(): void {
    this.#closed = true;
    this.#worker?.terminate();
    this.#worker = undefined;
    this.#fail(new Error("Browser highlighter was closed"));
  }
}
