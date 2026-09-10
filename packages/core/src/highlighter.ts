import type { HighlightRequest, SemanticPack } from "./pack.js";
import { PackRegistry } from "./registry.js";
import type { HighlightResult } from "./result.js";

export interface Highlighter {
  highlight(request: HighlightRequest): Promise<HighlightResult>;

  supports(documentKind: string): boolean;

  documentKinds(): readonly string[];
}

export interface CreateHighlighterOptions {
  packs: readonly SemanticPack[];
}

export function createHighlighter(options: CreateHighlighterOptions): Highlighter {
  const registry = new PackRegistry();
  const documentKinds = new Set<string>();

  for (const pack of options.packs) {
    registry.register(pack);

    for (const documentKind of pack.manifest.documentKinds) {
      documentKinds.add(documentKind.id);
    }
  }

  return {
    async highlight(request) {
      const pack = registry.get(request.documentKind);

      if (!pack) {
        throw new Error(`Unsupported document kind "${request.documentKind}".`);
      }

      return pack.highlight(request);
    },

    supports(documentKind) {
      return registry.get(documentKind) !== undefined;
    },

    documentKinds() {
      return [...documentKinds];
    },
  };
}
