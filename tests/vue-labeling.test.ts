import { readFile } from "node:fs/promises";

import type { SemanticSpan } from "@nsh/core";
import { describe, expect, it } from "vitest";

import { labelVue } from "../packs/vue/labeling/label.js";

const cases = JSON.parse(
  await readFile(new URL("../packs/vue/fixtures/golden.json", import.meta.url), "utf8"),
) as { id: string; profile: string; documentKind: string; markedSource: string }[];
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
describe("Vue versioned offline Gold", () => {
  it("accepts Vue SFC self-closing components and native tags", () => {
    const source = '<template><Panel :open="open"/><div/></template>';
    const gold = labelVue({ source, documentKind: "vue" });
    expect(
      gold.spans.filter(
        (s) => s.tokenType === "punctuation" && source.slice(s.start, s.end) === "/>",
      ),
    ).toHaveLength(2);
  });
  for (const c of cases)
    it(c.profile + ": " + c.id, () => {
      const gold = unmark(c.markedSource),
        actual = labelVue({ source: gold.source, documentKind: c.documentKind });
      expect(actual.offsetEncoding).toBe("utf-16");
      expect(actual.spans).toEqual(gold.spans);
      expect(
        actual.regions.map((r) => ({
          start: r.start,
          end: r.end,
          tokenType: "embedded-" + r.language,
        })),
      ).toEqual(gold.spans.filter((s) => s.tokenType.startsWith("embedded-")));
    });
  it("rejects parser failures and unsupported document kinds", () => {
    for (const source of [
      '<template><p title="unfinished></p></template>',
      "<script>const x = ;</script>",
      "<template>{{ foo( }}</template>",
    ])
      expect(() => labelVue({ source, documentKind: "vue" })).toThrow();
    expect(() => labelVue({ source: "<p>x</p>", documentKind: "html" })).toThrow();
  });
  it("keeps v-pre source text and never resolves src", () => {
    const result = labelVue({
      source:
        '<template><p v-pre>{{ literal }}</p></template><script src="./never-run.js"></script>',
      documentKind: "vue",
    });
    expect(result.regions).toEqual([]);
    expect(result.spans.some((s) => s.tokenType === "text")).toBe(true);
  });
});
