import type { HighlightRequest, HighlightResult, SemanticPack } from "@nsh/core";
import { describe, expect, it } from "vitest";

import { composeSvelteGold } from "../packs/svelte/labeling/embedded.js";
import {
  createCompositeSveltePack,
  EXPRESSION_PREFIX,
  EXPRESSION_SUFFIX,
} from "../packs/svelte/runtime/composite.js";

const manifest = { id: "svelte", documentKinds: [{ id: "svelte", extensions: [".svelte"] }] };
const base = (result: HighlightResult): SemanticPack => ({
  manifest,
  highlight: async () => result,
});
describe("Svelte predicted-region composition", () => {
  it("routes existing code models and projects wrapped expressions to original UTF-16", async () => {
    const source = "🌌 abc def ghi jkl mno pqr";
    const roles = ["javascript", "typescript", "css", "scss", "less", "expression"];
    const requests: HighlightRequest[] = [];
    const pack = createCompositeSveltePack({
      base: base({
        offsetEncoding: "utf-16",
        spans: roles.map((r, i) => ({
          start: 3 + 4 * i,
          end: 6 + 4 * i,
          tokenType: "embedded-" + r,
        })),
      }),
      highlightEmbedded: async (request) => {
        requests.push(request);
        const expression = request.source.startsWith(EXPRESSION_PREFIX);
        return {
          offsetEncoding: "utf-16",
          spans: [
            {
              start: expression ? EXPRESSION_PREFIX.length : 0,
              end: request.source.length - (expression ? EXPRESSION_SUFFIX.length : 0),
              tokenType: "variable",
            },
          ],
        };
      },
    });
    const result = await pack.highlight({ source, documentKind: "svelte" });
    expect(requests.map((r) => r.documentKind)).toEqual([
      "javascript",
      "typescript",
      "css",
      "scss",
      "less",
      "typescript",
    ]);
    expect(requests.at(-1)?.source).toBe(EXPRESSION_PREFIX + "pqr" + EXPRESSION_SUFFIX);
    expect(result.spans.at(-1)).toEqual({
      start: 23,
      end: 26,
      tokenType: "variable",
      documentKind: "typescript",
    });
  });
  it("does not infer regions from source tags, directives or external imports", async () => {
    const source = '<script src="https://example.invalid/app.ts">x</script>{name}';
    let calls = 0;
    const pack = createCompositeSveltePack({
      base: base({
        offsetEncoding: "utf-16",
        spans: [{ start: 0, end: source.length, tokenType: "text" }],
      }),
      highlightEmbedded: async () => {
        calls++;
        throw Error("unused");
      },
    });
    expect((await pack.highlight({ source, documentKind: "svelte" })).spans[0]?.tokenType).toBe(
      "text",
    );
    expect(calls).toBe(0);
  });
  it("leaves opaque preprocessors intact", async () => {
    const spans = [{ start: 0, end: 6, tokenType: "embedded-data" }];
    const pack = createCompositeSveltePack({
      base: base({ offsetEncoding: "utf-16", spans }),
      highlightEmbedded: async () => {
        throw Error("unused");
      },
    });
    expect((await pack.highlight({ source: "opaque", documentKind: "svelte" })).spans).toEqual(
      spans,
    );
  });
  it("rejects overlap, out-of-bounds and split surrogate offsets", async () => {
    for (const spans of [
      [{ start: 1, end: 2, tokenType: "text" }],
      [{ start: 0, end: 4, tokenType: "text" }],
      [
        { start: 0, end: 3, tokenType: "text" },
        { start: 2, end: 3, tokenType: "text" },
      ],
    ]) {
      const pack = createCompositeSveltePack({
        base: base({ offsetEncoding: "utf-16", spans }),
        highlightEmbedded: async () => {
          throw Error("unused");
        },
      });
      await expect(pack.highlight({ source: "🌌x", documentKind: "svelte" })).rejects.toThrow();
    }
  });
  it("validates child offsets and propagates child failures", async () => {
    for (const highlightEmbedded of [
      async () => ({
        offsetEncoding: "utf-16" as const,
        spans: [{ start: 0, end: 2, tokenType: "variable" }],
      }),
      async () => {
        throw Error("child failed");
      },
    ]) {
      const pack = createCompositeSveltePack({
        base: base({
          offsetEncoding: "utf-16",
          spans: [{ start: 0, end: 1, tokenType: "embedded-typescript" }],
        }),
        highlightEmbedded,
      });
      await expect(pack.highlight({ source: "x", documentKind: "svelte" })).rejects.toThrow();
    }
  });
  it("clips fixed wrapper tokens and rejects unrelated document kinds", async () => {
    const pack = createCompositeSveltePack({
      base: base({
        offsetEncoding: "utf-16",
        spans: [{ start: 0, end: 1, tokenType: "embedded-expression" }],
      }),
      highlightEmbedded: async ({ source }) => ({
        offsetEncoding: "utf-16",
        spans: [{ start: 0, end: source.length, tokenType: "variable" }],
      }),
    });
    expect((await pack.highlight({ source: "x", documentKind: "svelte" })).spans).toEqual([
      { start: 0, end: 1, tokenType: "variable", documentKind: "typescript" },
    ]);
    await expect(pack.highlight({ source: "x", documentKind: "html" })).rejects.toThrow();
  });
  it("builds separate offline JS/TS/CSS references without inference cuts", () => {
    const source = "const x = 1;";
    const r = composeSvelteGold(source, {
      offsetEncoding: "utf-16",
      spans: [{ start: 0, end: source.length, tokenType: "embedded-typescript" }],
    });
    expect(
      r.spans.some((s) => s.tokenType === "variable" && source.slice(s.start, s.end) === "x"),
    ).toBe(true);
  });
});
