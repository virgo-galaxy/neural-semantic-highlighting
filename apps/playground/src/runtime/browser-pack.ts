import type { SemanticPack } from "@nsh/core";
import { createHighlighter } from "@nsh/highlighter/bundled";

export interface PlaygroundBrowserPack extends SemanticPack {
  close(): void;
}

export async function createBrowserSemanticPack(): Promise<PlaygroundBrowserPack> {
  const highlighter = createHighlighter();
  return {
    manifest: {
      id: "playground-browser",
      documentKinds: highlighter.languages().map((id) => ({ id, extensions: [] })),
    },
    highlight: (request) => highlighter.highlightTokens(request),
    close: () => highlighter.close(),
  };
}
