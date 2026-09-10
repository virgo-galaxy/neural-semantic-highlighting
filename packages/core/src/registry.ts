import type { SemanticPack } from "./pack.js";

export class PackRegistry {
  private readonly packs = new Map<string, SemanticPack>();

  register(pack: SemanticPack): void {
    for (const documentKind of pack.manifest.documentKinds) {
      if (this.packs.has(documentKind.id)) {
        throw new Error(`Document kind "${documentKind.id}" is already registered.`);
      }

      this.packs.set(documentKind.id, pack);
    }
  }

  get(documentKind: string): SemanticPack | undefined {
    return this.packs.get(documentKind);
  }
}
