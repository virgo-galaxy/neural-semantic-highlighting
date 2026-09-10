import { readdir, readFile } from "node:fs/promises";

import type { HighlightResult, PackManifest, PackSchema, SemanticSpan } from "@nsh/core";
import { describe, expect, it } from "vitest";

interface GoldSpan extends SemanticSpan {
  text: string;
}

interface GoldFixture extends Omit<HighlightResult, "spans"> {
  documentKind: string;
  spans: GoldSpan[];
}

const packUrl = new URL("../packs/typescript/", import.meta.url);
const fixturesUrl = new URL("fixtures/", packUrl);

const manifest = JSON.parse(
  await readFile(new URL("manifest.json", packUrl), "utf8"),
) as PackManifest;

const schema = JSON.parse(await readFile(new URL("schema.json", packUrl), "utf8")) as PackSchema;

const fixtureEntries = await readdir(fixturesUrl, {
  withFileTypes: true,
});

const fixtureNames = fixtureEntries
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);

const documentKinds = new Set(manifest.documentKinds.map((kind) => kind.id));
const tokenTypes = new Set(schema.tokenTypes.map((tokenType) => tokenType.id));
const tokenModifiers = new Set(schema.tokenModifiers.map((modifier) => modifier.id));

describe("TypeScript gold fixtures", () => {
  for (const fixtureName of fixtureNames) {
    it(`validates ${fixtureName}`, async () => {
      const fixtureUrl = new URL(`${fixtureName}/`, fixturesUrl);
      const files = await readdir(fixtureUrl);

      const sourceFiles = files.filter((file) => file === "source" || file.startsWith("source."));

      expect(sourceFiles).toHaveLength(1);

      const sourceFile = sourceFiles[0];

      if (!sourceFile) {
        throw new Error(`Fixture "${fixtureName}" does not contain a source file.`);
      }

      const source = await readFile(new URL(sourceFile, fixtureUrl), "utf8");

      const expected = JSON.parse(
        await readFile(new URL("expected.json", fixtureUrl), "utf8"),
      ) as GoldFixture;

      expect(documentKinds.has(expected.documentKind)).toBe(true);
      expect(expected.offsetEncoding).toBe("utf-16");

      let previousEnd = 0;

      for (const span of expected.spans) {
        expect(Number.isInteger(span.start)).toBe(true);
        expect(Number.isInteger(span.end)).toBe(true);

        expect(span.start).toBeGreaterThanOrEqual(0);
        expect(span.start).toBeGreaterThanOrEqual(previousEnd);
        expect(span.end).toBeGreaterThan(span.start);
        expect(span.end).toBeLessThanOrEqual(source.length);

        expect(source.slice(span.start, span.end)).toBe(span.text);

        expect(tokenTypes.has(span.tokenType)).toBe(true);

        for (const modifier of span.modifiers ?? []) {
          expect(tokenModifiers.has(modifier)).toBe(true);
        }

        previousEnd = span.end;
      }
    });
  }
});
