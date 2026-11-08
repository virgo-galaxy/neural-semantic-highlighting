import { readFile } from "node:fs/promises";

import type { PackSchema, SemanticSpan } from "@nsh/core";
import { describe, expect, it } from "vitest";

import { labelHtml } from "../packs/html/labeling/label.js";

interface Golden {
  id: string;
  documentKind: string;
  markedSource: string;
}
const root = new URL("../packs/html/", import.meta.url);
const fixtures = JSON.parse(
  await readFile(new URL("fixtures/golden.json", root), "utf8"),
) as Golden[];
const schema = JSON.parse(await readFile(new URL("schema.json", root), "utf8")) as PackSchema;

function unmark(marked: string) {
  let source = "",
    cursor = 0;
  const spans: SemanticSpan[] = [];
  for (const match of marked.matchAll(/⟦([^|]+)\|([\s\S]*?)⟧/gu)) {
    source += marked.slice(cursor, match.index);
    const [tokenType, ...modifiers] = match[1]!.split("+");
    const start = source.length;
    source += match[2]!;
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

describe("modern HTML offline Gold", () => {
  for (const fixture of fixtures) {
    it("matches independent Golden: " + fixture.id, async () => {
      const expected = unmark(fixture.markedSource);
      const result = await labelHtml({
        source: expected.source,
        documentKind: fixture.documentKind,
      });
      expect(result.offsetEncoding).toBe("utf-16");
      expect(result.spans).toEqual(expected.spans);
      expect(result.modernExclusions).toEqual([]);
      expect(result.regions).toEqual(
        expected.spans
          .filter((span) => span.tokenType.startsWith("embedded-"))
          .map((span) => ({
            start: span.start,
            end: span.end,
            language: span.tokenType.slice("embedded-".length),
            context: "block",
          })),
      );
      const boundaries = new Set<number>([0]);
      let unit = 0;
      for (const character of expected.source) {
        unit += character.length;
        boundaries.add(unit);
      }
      for (const span of result.spans) {
        expect(boundaries.has(span.start) && boundaries.has(span.end)).toBe(true);
        expect(schema.tokenTypes.some((type) => type.id === span.tokenType)).toBe(true);
      }
    });
  }

  it("rejects lexical gaps, malformed comments and unfinished script bodies", async () => {
    for (const source of [
      '<div title="unfinished>',
      "<!-- unfinished",
      "<script>const x=1",
      "<p x=>",
    ])
      await expect(labelHtml({ source, documentKind: "html" })).rejects.toThrow();
    await expect(labelHtml({ source: "<p>x</p>", documentKind: "vue" })).rejects.toThrow();
  });

  it("records obsolete training exclusions without a small allowed-tag vocabulary", async () => {
    expect(
      (await labelHtml({ source: "<center>x</center>", documentKind: "html" })).modernExclusions,
    ).toEqual(["obsolete-element:center"]);
    expect(
      (
        await labelHtml({
          source: "<search><b>x</b><i>y</i><small>z</small></search>",
          documentKind: "html",
        })
      ).modernExclusions,
    ).toEqual([]);
  });

  it("never fetches resources or treats unknown script types as JavaScript", async () => {
    const source =
      '<script src="https://example.invalid/x.js"></script><script type="importmap">{"imports":{}}</script><style type="text/scss">$x:1;</style>';
    const result = await labelHtml({ source, documentKind: "html" });
    expect(result.regions.map((region) => region.language)).toEqual(["data", "data"]);
  });
});
