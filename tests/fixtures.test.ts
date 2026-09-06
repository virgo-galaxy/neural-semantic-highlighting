import { readFile } from "node:fs/promises";

import { describe, expect, it } from "vitest";

import type { HighlightResult } from "../src/core/result.js";

interface GoldFixture extends HighlightResult {
  documentKind: string;
}

describe("TypeScript gold fixtures", () => {
  it("validates variable declaration", async () => {
    const fixture = new URL("../packs/typescript/fixtures/variable-declaration/", import.meta.url);

    const source = await readFile(new URL("source.ts", fixture), "utf8");

    const expected = JSON.parse(
      await readFile(new URL("expected.json", fixture), "utf8"),
    ) as GoldFixture;

    expect(expected.documentKind).toBe("typescript");
    expect(expected.offsetEncoding).toBe("utf-16");

    for (const span of expected.spans) {
      expect(Number.isInteger(span.start)).toBe(true);
      expect(Number.isInteger(span.end)).toBe(true);

      expect(span.start).toBeGreaterThanOrEqual(0);
      expect(span.end).toBeGreaterThan(span.start);
      expect(span.end).toBeLessThanOrEqual(source.length);
    }
  });
});
