import { readdir, readFile } from "node:fs/promises";

import type { HighlightResult, SemanticSpan } from "@nsh/core";
import { describe, expect, it } from "vitest";

import { labelTypeScript } from "../packs/typescript/labeling/label.js";

interface GoldSpan extends SemanticSpan {
  text: string;
}

interface GoldFixture extends Omit<HighlightResult, "spans"> {
  documentKind: string;
  spans: GoldSpan[];
}

const fixturesUrl = new URL("../packs/typescript/fixtures/", import.meta.url);

const fixtureEntries = await readdir(fixturesUrl, {
  withFileTypes: true,
});

const fixtureNames = fixtureEntries
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name)
  .sort();

function toHighlightResult(expected: GoldFixture): HighlightResult {
  return {
    offsetEncoding: expected.offsetEncoding,
    spans: expected.spans.map((span) => ({
      start: span.start,
      end: span.end,
      tokenType: span.tokenType,
      ...(span.modifiers
        ? {
            modifiers: span.modifiers,
          }
        : {}),
    })),
  };
}

describe("TypeScript labeler", () => {
  for (const fixtureName of fixtureNames) {
    it(`matches ${fixtureName}`, async () => {
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

      const actual = labelTypeScript({
        source,
        documentKind: expected.documentKind,
      });

      expect(actual).toEqual(toHighlightResult(expected));
    });
  }
});
