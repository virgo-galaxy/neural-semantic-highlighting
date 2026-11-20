import { createHighlighter, type Highlighter } from "@nsh/core";

import {
  createBrowserSemanticPack,
  type PlaygroundBrowserPack,
  type PlaygroundModelSource,
} from "./browser-pack.js";

/** One source generation owns its pack; late initialization cannot replace a newer one. */
export class PlaygroundRuntimeManager {
  #generation = 0;
  #closed = false;
  #pending?: Promise<Highlighter>;
  #pack?: PlaygroundBrowserPack;
  readonly #create: (settings: PlaygroundModelSource) => Promise<PlaygroundBrowserPack>;
  constructor(create = createBrowserSemanticPack) {
    this.#create = create;
  }
  get(settings: PlaygroundModelSource): Promise<Highlighter> {
    if (this.#closed) return Promise.reject(new Error("Playground runtime is closed"));
    if (!this.#pending) {
      const generation = this.#generation;
      this.#pending = this.#create({ ...settings })
        .then((pack) => {
          if (this.#closed || generation !== this.#generation) {
            pack.close();
            throw new Error("Playground model source changed");
          }
          this.#pack = pack;
          return createHighlighter({ packs: [pack] });
        })
        .catch((error: unknown) => {
          if (generation === this.#generation) this.#pending = undefined;
          throw error;
        });
    }
    return this.#pending;
  }
  reset(): void {
    this.#generation++;
    this.#pack?.close();
    this.#pack = undefined;
    this.#pending = undefined;
  }
  close(): void {
    this.#closed = true;
    this.reset();
  }
}
