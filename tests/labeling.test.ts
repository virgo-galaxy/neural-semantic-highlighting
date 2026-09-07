import { readFile } from "node:fs/promises";

import { describe, expect, it } from "vitest";

import type { HighlightResult, SemanticSpan } from "@/core/result.js";

import { labelTypeScript } from "../packs/typescript/labeling/label.js";

interface GoldSpan extends SemanticSpan {
  text: string;
}

interface GoldFixture extends Omit<HighlightResult, "spans"> {
  documentKind: string;
  spans: GoldSpan[];
}

describe("TypeScript labeler", () => {
  it("matches the variable declaration gold fixture", async () => {
    const fixtureUrl = new URL(
      "../packs/typescript/fixtures/variable-declaration/",
      import.meta.url,
    );

    const source = await readFile(new URL("source.ts", fixtureUrl), "utf8");

    const expected = JSON.parse(
      await readFile(new URL("expected.json", fixtureUrl), "utf8"),
    ) as GoldFixture;

    const actual = labelTypeScript({
      source,
      documentKind: expected.documentKind,
    });

    const expectedResult: HighlightResult = {
      offsetEncoding: expected.offsetEncoding,
      spans: expected.spans.map((span) => ({
        start: span.start,
        end: span.end,
        tokenType: span.tokenType,
        ...(span.modifiers ? { modifiers: span.modifiers } : {}),
      })),
    };

    expect(actual).toEqual(expectedResult);
  });
});
