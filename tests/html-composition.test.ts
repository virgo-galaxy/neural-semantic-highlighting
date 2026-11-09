import type { HighlightResult, SemanticPack } from "@nsh/core";
import { describe, expect, it, vi } from "vitest";

import { composeHtmlGold } from "../packs/html/labeling/embedded.js";
import { labelHtml } from "../packs/html/labeling/label.js";
import { createCompositeHtmlPack } from "../packs/html/runtime/composite.js";

function base(result: HighlightResult): SemanticPack {
  return {
    manifest: { id: "html", documentKinds: [{ id: "html", extensions: [".html"] }] },
    highlight: async () => result,
  };
}

describe("HTML neural region composition", () => {
  it("offline composed Gold preserves independently checked HTML, CSS and JavaScript roles", async () => {
    const source = '<style>.card{color:red;}</style><script>const count = "<b>";</script>';
    const result = composeHtmlGold(source, await labelHtml({ source, documentKind: "html" }));
    const values = result.spans.map((span) => ({
      text: source.slice(span.start, span.end),
      role: span.tokenType,
      modifiers: span.modifiers ?? [],
    }));
    expect(values).toContainEqual({ text: "color", role: "property", modifiers: ["declaration"] });
    expect(
      values.some(
        (span) =>
          span.text === "count" &&
          span.role === "variable" &&
          span.modifiers.includes("declaration"),
      ),
    ).toBe(true);
    expect(values).toContainEqual({ text: '"<b>"', role: "string", modifiers: [] });
    expect(values).toContainEqual({ text: "style", role: "tag", modifiers: ["closing"] });
    expect(values.some((span) => span.role.startsWith("embedded-"))).toBe(false);
  });

  it("offline composition quarantines invalid embedded syntax", async () => {
    const source = "<script>const count = ;</script>";
    const baseGold = await labelHtml({ source, documentKind: "html" });
    expect(() => composeHtmlGold(source, baseGold)).toThrow("syntax");
  });
  it("calls the matching existing pack and restores original UTF-16 offsets and modifiers", async () => {
    const source = "🌌<style>.x{color:red}</style><script>let x=1;</script>";
    const css = source.indexOf(".x{"),
      js = source.indexOf("let x");
    const provider = vi.fn(async ({ documentKind }: { documentKind: string }) => ({
      offsetEncoding: "utf-16" as const,
      spans:
        documentKind === "css"
          ? [{ start: 3, end: 8, tokenType: "property", modifiers: ["declaration"] }]
          : [{ start: 4, end: 5, tokenType: "variable", modifiers: ["declaration"] }],
    }));
    const pack = createCompositeHtmlPack({
      base: base({
        offsetEncoding: "utf-16",
        spans: [
          { start: css, end: css + ".x{color:red}".length, tokenType: "embedded-css" },
          { start: js, end: js + "let x=1;".length, tokenType: "embedded-javascript" },
        ],
      }),
      highlightEmbedded: provider,
    });
    const result = await pack.highlight({ source, documentKind: "html" });
    expect(provider.mock.calls.map(([request]) => request.documentKind)).toEqual([
      "css",
      "javascript",
    ]);
    expect(result.spans).toEqual([
      {
        start: css + 3,
        end: css + 8,
        tokenType: "property",
        modifiers: ["declaration"],
        documentKind: "css",
      },
      {
        start: js + 4,
        end: js + 5,
        tokenType: "variable",
        modifiers: ["declaration"],
        documentKind: "javascript",
      },
    ]);
    expect(source.slice(result.spans[0]!.start, result.spans[0]!.end)).toBe("color");
  });

  it("does not infer regions from source spellings or reinterpret data and attribute strings", async () => {
    const source = '<div title="<script>" style="color:red">{"x":1}</div>';
    const provider = vi.fn(async () => {
      throw new Error("must not invoke");
    });
    const result: HighlightResult = {
      offsetEncoding: "utf-16",
      spans: [
        { start: 11, end: 19, tokenType: "string" },
        { start: 38, end: 45, tokenType: "embedded-data" },
      ],
    };
    const pack = createCompositeHtmlPack({ base: base(result), highlightEmbedded: provider });
    expect(await pack.highlight({ source, documentKind: "html" })).toEqual(result);
    expect(provider).not.toHaveBeenCalled();
  });

  it("rejects invalid child offsets, overlap, encodings and surrogate splits", async () => {
    for (const child of [
      { offsetEncoding: "utf-8", spans: [] },
      { offsetEncoding: "utf-16", spans: [{ start: 0, end: 99, tokenType: "string" }] },
      { offsetEncoding: "utf-16", spans: [{ start: 1, end: 2, tokenType: "string" }] },
      {
        offsetEncoding: "utf-16",
        spans: [
          { start: 0, end: 2, tokenType: "string" },
          { start: 0, end: 1, tokenType: "tag" },
        ],
      },
    ] as HighlightResult[]) {
      const pack = createCompositeHtmlPack({
        base: base({
          offsetEncoding: "utf-16",
          spans: [{ start: 0, end: 3, tokenType: "embedded-css" }],
        }),
        highlightEmbedded: async () => child,
      });
      await expect(pack.highlight({ source: "🌌x", documentKind: "html" })).rejects.toThrow();
    }
  });

  it("propagates provider failure instead of reporting successful mixed-language highlighting", async () => {
    const pack = createCompositeHtmlPack({
      base: base({
        offsetEncoding: "utf-16",
        spans: [{ start: 0, end: 1, tokenType: "embedded-javascript" }],
      }),
      highlightEmbedded: async () => {
        throw new Error("model unavailable");
      },
    });
    await expect(pack.highlight({ source: "x", documentKind: "html" })).rejects.toThrow(
      "model unavailable",
    );
  });
});
