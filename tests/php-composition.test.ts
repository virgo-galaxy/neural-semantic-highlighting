import type { HighlightResult, SemanticPack } from "@nsh/core";
import { createCompositePhpPack } from "@nsh/core/composition/php";
import { describe, expect, it, vi } from "vitest";

function base(result: HighlightResult): SemanticPack {
  return {
    manifest: { id: "php", documentKinds: [{ id: "php", extensions: [".php", ".phtml"] }] },
    highlight: vi.fn(async () => result),
  };
}

describe("PHP composition", () => {
  it("uses predicted HTML ranges and preserves child language/UTF-16 offsets", async () => {
    const child = vi.fn(async () => ({
      offsetEncoding: "utf-16" as const,
      spans: [{ start: 0, end: 2, tokenType: "string", documentKind: "javascript" }],
    }));
    const pack = createCompositePhpPack({
      base: base({
        offsetEncoding: "utf-16",
        spans: [
          { start: 0, end: 2, tokenType: "keyword" },
          { start: 2, end: 4, tokenType: "embedded-html" },
        ],
      }),
      highlightEmbedded: child,
    });
    const result = await pack.highlight({ source: "?>🌌", documentKind: "php" });
    expect(child).toHaveBeenCalledWith({ source: "🌌", documentKind: "html" });
    expect(result.spans).toEqual([
      { start: 0, end: 2, tokenType: "keyword" },
      { start: 2, end: 4, tokenType: "string", documentKind: "javascript" },
    ]);
  });
  it("does not infer regions from PHP/HTML-looking source spelling", async () => {
    const child = vi.fn();
    const pack = createCompositePhpPack({
      base: base({ offsetEncoding: "utf-16", spans: [{ start: 0, end: 5, tokenType: "string" }] }),
      highlightEmbedded: child,
    });
    await pack.highlight({ source: "<?php", documentKind: "php" });
    expect(child).not.toHaveBeenCalled();
  });
  it("leaves separate predictions separate and preserves the original text", async () => {
    const child = vi.fn(async () => ({ offsetEncoding: "utf-16" as const, spans: [] }));
    const pack = createCompositePhpPack({
      base: base({
        offsetEncoding: "utf-16",
        spans: [
          { start: 0, end: 1, tokenType: "embedded-html" },
          { start: 1, end: 2, tokenType: "keyword" },
          { start: 2, end: 3, tokenType: "embedded-html" },
        ],
      }),
      highlightEmbedded: child,
    });
    await pack.highlight({ source: "abc", documentKind: "php" });
    expect(child.mock.calls).toEqual([
      [{ source: "a", documentKind: "html" }],
      [{ source: "c", documentKind: "html" }],
    ]);
  });
  it("rejects overlapping base spans and surrogate-splitting child spans", async () => {
    const child = vi.fn(async () => ({
      offsetEncoding: "utf-16" as const,
      spans: [{ start: 0, end: 1, tokenType: "text" }],
    }));
    const overlapping = createCompositePhpPack({
      base: base({
        offsetEncoding: "utf-16",
        spans: [
          { start: 0, end: 2, tokenType: "string" },
          { start: 1, end: 2, tokenType: "embedded-html" },
        ],
      }),
      highlightEmbedded: child,
    });
    await expect(overlapping.highlight({ source: "🌌", documentKind: "php" })).rejects.toThrow();
    expect(child).not.toHaveBeenCalled();
    const splitting = createCompositePhpPack({
      base: base({
        offsetEncoding: "utf-16",
        spans: [{ start: 0, end: 2, tokenType: "embedded-html" }],
      }),
      highlightEmbedded: child,
    });
    await expect(splitting.highlight({ source: "🌌", documentKind: "php" })).rejects.toThrow();
  });
  it("rejects unrelated document kinds", async () => {
    const pack = createCompositePhpPack({
      base: base({ offsetEncoding: "utf-16", spans: [] }),
      highlightEmbedded: vi.fn(),
    });
    await expect(pack.highlight({ source: "", documentKind: "html" })).rejects.toThrow();
  });
});

it("offline composed PHP template Gold retains HTML and CSS roles", async () => {
  const { composePhpGold } = await import("../packs/php/labeling/compose-gold.js");
  const source = "<style>.card{color:red;}</style><p><?= $title ?></p>";
  const open = source.indexOf("<?="),
    close = source.indexOf("?>");
  const result = await composePhpGold(source, {
    offsetEncoding: "utf-16",
    spans: [
      { start: 0, end: open, tokenType: "embedded-html" },
      { start: open, end: open + 3, tokenType: "keyword" },
      { start: open + 4, end: close - 1, tokenType: "variable" },
      { start: close, end: close + 2, tokenType: "keyword" },
      { start: close + 2, end: source.length, tokenType: "embedded-html" },
    ],
  });
  expect(
    result.spans.some(
      (span) =>
        source.slice(span.start, span.end) === "color" &&
        span.tokenType === "property" &&
        span.documentKind === "css",
    ),
  ).toBe(true);
  expect(
    result.spans.some(
      (span) => span.tokenType === "tag" && source.slice(span.start, span.end) === "p",
    ),
  ).toBe(true);
  expect(result.spans.some((span) => span.tokenType.startsWith("embedded-"))).toBe(false);
});
