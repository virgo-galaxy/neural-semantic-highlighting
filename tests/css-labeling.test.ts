import { readFile } from "node:fs/promises";

import type { PackManifest, PackSchema, SemanticSpan } from "@nsh/core";
import { describe, expect, it } from "vitest";

import { labelCss } from "../packs/css/labeling/label.js";

interface Golden {
  id: string;
  documentKind: string;
  markedSource: string;
}

const root = new URL("../packs/css/", import.meta.url);
const cases = JSON.parse(await readFile(new URL("fixtures/golden.json", root), "utf8")) as Golden[];
const schema = JSON.parse(await readFile(new URL("schema.json", root), "utf8")) as PackSchema;
const manifest = JSON.parse(await readFile(new URL("manifest.json", root), "utf8")) as PackManifest;

function unmark(marked: string): { source: string; spans: SemanticSpan[] } {
  let source = "";
  let cursor = 0;
  const spans: SemanticSpan[] = [];
  for (const match of marked.matchAll(/⟦([^|]+)\|([\s\S]*?)⟧/gu)) {
    source += marked.slice(cursor, match.index);
    const [tokenType, ...modifiers] = match[1]!.split("+");
    const text = match[2]!;
    const start = source.length;
    source += text;
    spans.push({
      start,
      end: source.length,
      tokenType: tokenType!,
      ...(modifiers.length ? { modifiers } : {}),
    });
    cursor = match.index + match[0].length;
  }
  return { source: source + marked.slice(cursor), spans };
}

describe("CSS family offline Gold", () => {
  for (const fixture of cases) {
    it("matches independent Golden: " + fixture.id, () => {
      const expected = unmark(fixture.markedSource);
      const result = labelCss({ source: expected.source, documentKind: fixture.documentKind });
      expect(result.offsetEncoding).toBe("utf-16");
      expect(result.spans).toEqual(expected.spans);
      const types = new Set(schema.tokenTypes.map((type) => type.id));
      const modifiers = new Set(schema.tokenModifiers.map((modifier) => modifier.id));
      expect(manifest.documentKinds.some((kind) => kind.id === fixture.documentKind)).toBe(true);
      let end = 0;
      for (const span of result.spans) {
        expect(expected.source.slice(end, span.start).trim()).toBe("");
        expect(span.start).toBeGreaterThanOrEqual(end);
        expect(span.end).toBeGreaterThan(span.start);
        expect(types.has(span.tokenType)).toBe(true);
        for (const modifier of span.modifiers ?? []) expect(modifiers.has(modifier)).toBe(true);
        end = span.end;
      }
      expect(expected.source.slice(end).trim()).toBe("");
    });
  }

  it("rejects syntax errors and unsupported kinds instead of emitting partial Gold", () => {
    expect(() => labelCss({ source: ".x { color: red;", documentKind: "css" })).toThrow();
    expect(() => labelCss({ source: "a {", documentKind: "scss" })).toThrow();
    expect(() => labelCss({ source: ".x {}", documentKind: "stylus" })).toThrow();
    expect(() => labelCss({ source: "$gap: 1px;", documentKind: "css" })).toThrow();
  });

  it("keeps raw URL slashes separate from following Sass line comments", () => {
    const source = ".x { background: url(https://example.invalid/a.png); color: red; } // end";
    const { spans } = labelCss({ source, documentKind: "scss" });
    expect(
      spans
        .filter((span) => span.tokenType === "comment")
        .map((span) => source.slice(span.start, span.end)),
    ).toEqual(["// end"]);
    expect(
      spans.some(
        (span) => source.slice(span.start, span.end) === "color" && span.tokenType === "property",
      ),
    ).toBe(true);
  });
});
