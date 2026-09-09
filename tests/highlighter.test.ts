import { describe, expect, it } from "vitest";

import { createHighlighter, type HighlightResult, type SemanticPack } from "../src/index.js";

const result: HighlightResult = {
  offsetEncoding: "utf-16",
  spans: [],
};

const pack: SemanticPack = {
  manifest: {
    id: "test-pack",
    documentKinds: [
      {
        id: "typescript",
        extensions: [".ts"],
      },
      {
        id: "tsx",
        extensions: [".tsx"],
      },
    ],
  },

  async highlight() {
    return result;
  },
};

describe("createHighlighter", () => {
  it("routes requests to the registered semantic pack", async () => {
    const highlighter = createHighlighter({
      packs: [pack],
    });

    await expect(
      highlighter.highlight({
        source: "const value = 1;",
        documentKind: "typescript",
      }),
    ).resolves.toEqual(result);
  });

  it("reports supported document kinds", () => {
    const highlighter = createHighlighter({
      packs: [pack],
    });

    expect(highlighter.supports("typescript")).toBe(true);
    expect(highlighter.supports("tsx")).toBe(true);
    expect(highlighter.supports("python")).toBe(false);
  });

  it("lists registered document kinds", () => {
    const highlighter = createHighlighter({
      packs: [pack],
    });

    expect(highlighter.documentKinds()).toEqual(["typescript", "tsx"]);
  });

  it("rejects unsupported document kinds", async () => {
    const highlighter = createHighlighter({
      packs: [pack],
    });

    await expect(
      highlighter.highlight({
        source: "print('hello')",
        documentKind: "python",
      }),
    ).rejects.toThrow('Unsupported document kind "python".');
  });
});
