import type { HighlightResult, SemanticPack } from "@nsh/core";
import { normalizeLanguageId } from "@nsh/core";
import { createCompositeMarkdownPack } from "@nsh/core/composition/markdown";
import { describe, expect, it, vi } from "vitest";

const source = "# 星空 🌌\r\n\r\n```JS\r\nconst title = '星空';\r\n```\r\n";
const bodyStart = source.indexOf("const");
const bodyEnd = source.lastIndexOf("```");
const info = source.indexOf("JS");
const result: HighlightResult = {
  offsetEncoding: "utf-16",
  spans: [
    { start: source.indexOf("```"), end: info, tokenType: "code-fence" },
    { start: info, end: info + 2, tokenType: "code-language" },
    { start: bodyStart, end: bodyEnd, tokenType: "embedded-code" },
    { start: bodyEnd, end: bodyEnd + 3, tokenType: "code-fence" },
  ],
};
function base(output = result): SemanticPack {
  return {
    manifest: { id: "markdown", documentKinds: [{ id: "markdown", extensions: [".md"] }] },
    highlight: async () => output,
  };
}
describe("Markdown predicted-region composition", () => {
  it("normalizes explicit IDs without treating inherited object keys as aliases", () => {
    expect(normalizeLanguageId("JS")).toBe("javascript");
    expect(normalizeLanguageId("MD")).toBe("markdown");
    expect(normalizeLanguageId("__proto__")).toBe("__proto__");
    expect(normalizeLanguageId("constructor")).toBe("constructor");
  });
  it("routes explicit info aliases and preserves original CRLF/Unicode child offsets", async () => {
    const highlightEmbedded = vi.fn(async () => ({
      offsetEncoding: "utf-16" as const,
      spans: [{ start: 0, end: 5, tokenType: "keyword" }],
    }));
    const pack = createCompositeMarkdownPack({
      base: base(),
      resolveLanguage: normalizeLanguageId,
      highlightEmbedded,
    });
    const output = await pack.highlight({ source, documentKind: "markdown" });
    expect(highlightEmbedded).toHaveBeenCalledExactlyOnceWith({
      source: source.slice(bodyStart, bodyEnd),
      documentKind: "javascript",
    });
    expect(output.spans).toContainEqual({
      start: bodyStart,
      end: bodyStart + 5,
      tokenType: "keyword",
      documentKind: "javascript",
    });
  });
  it("does not scan source fences when the model predicts ordinary text", async () => {
    const highlightEmbedded = vi.fn();
    const output = {
      offsetEncoding: "utf-16" as const,
      spans: [{ start: 0, end: source.length, tokenType: "text" }],
    };
    const pack = createCompositeMarkdownPack({
      base: base(output),
      resolveLanguage: normalizeLanguageId,
      highlightEmbedded,
    });
    expect(await pack.highlight({ source, documentKind: "markdown" })).toEqual(output);
    expect(highlightEmbedded).not.toHaveBeenCalled();
  });
  it.each([undefined, "markdown"])(
    "keeps unknown/unregistered and recursive %s fences as code",
    async (kind) => {
      const highlightEmbedded = vi.fn();
      const pack = createCompositeMarkdownPack({
        base: base(),
        resolveLanguage: () => kind,
        highlightEmbedded,
      });
      const output = await pack.highlight({ source, documentKind: "markdown" });
      expect(output.spans).toContainEqual({ start: bodyStart, end: bodyEnd, tokenType: "code" });
      expect(highlightEmbedded).not.toHaveBeenCalled();
    },
  );
  it("clears language state at delimiters and never reuses a preceding empty fence info", async () => {
    const output = {
      ...result,
      spans: [
        result.spans[0],
        result.spans[1],
        { start: bodyStart, end: bodyStart + 3, tokenType: "code-fence" },
        { start: bodyStart + 3, end: bodyEnd, tokenType: "embedded-code" },
      ],
    };
    const highlightEmbedded = vi.fn();
    const pack = createCompositeMarkdownPack({
      base: base(output),
      resolveLanguage: normalizeLanguageId,
      highlightEmbedded,
    });
    const predicted = await pack.highlight({ source, documentKind: "markdown" });
    expect(predicted.spans.at(-1)?.tokenType).toBe("code");
    expect(highlightEmbedded).not.toHaveBeenCalled();
  });
  it("rejects base offsets inside an astral character", async () => {
    const start = source.indexOf("🌌");
    const pack = createCompositeMarkdownPack({
      base: base({
        offsetEncoding: "utf-16",
        spans: [{ start: start + 1, end: start + 2, tokenType: "text" }],
      }),
      resolveLanguage: normalizeLanguageId,
      highlightEmbedded: vi.fn(),
    });
    await expect(pack.highlight({ source, documentKind: "markdown" })).rejects.toThrow("offsets");
  });
  it("rejects child offsets outside the predicted original body", async () => {
    const pack = createCompositeMarkdownPack({
      base: base(),
      resolveLanguage: normalizeLanguageId,
      highlightEmbedded: async () => ({
        offsetEncoding: "utf-16",
        spans: [{ start: 0, end: source.length, tokenType: "string" }],
      }),
    });
    await expect(pack.highlight({ source, documentKind: "markdown" })).rejects.toThrow("offsets");
  });
  it("rejects unrelated document kinds", async () => {
    const pack = createCompositeMarkdownPack({
      base: base(),
      resolveLanguage: normalizeLanguageId,
      highlightEmbedded: vi.fn(),
    });
    await expect(pack.highlight({ source, documentKind: "mdx" })).rejects.toThrow("document kind");
  });
});
