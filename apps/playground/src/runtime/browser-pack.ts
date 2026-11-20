import type { SemanticPack } from "@nsh/core";

export interface PlaygroundModelSource {
  mode: "local" | "remote";
  modelBaseUrl: string;
  persistent: boolean;
}
export const defaultModelSource: PlaygroundModelSource = {
  mode: "local",
  modelBaseUrl: "",
  persistent: true,
};

export interface PlaygroundBrowserPack extends SemanticPack {
  close(): void;
}

export async function createBrowserSemanticPack(
  options: PlaygroundModelSource = defaultModelSource,
): Promise<PlaygroundBrowserPack> {
  const cache = { persistent: options.persistent };
  const highlighter =
    options.mode === "remote"
      ? (await import("@nsh/highlighter")).createHighlighter({
          modelBaseUrl: options.modelBaseUrl,
          cache,
        })
      : (await import("@nsh/highlighter/bundled")).createHighlighter({ cache });
  return {
    manifest: {
      id: "playground-browser",
      documentKinds: highlighter.languages().map((id) => ({ id, extensions: [] })),
    },
    highlight: (request) => highlighter.highlightTokens(request),
    close: () => highlighter.close(),
  };
}
