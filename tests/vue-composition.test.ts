import type { HighlightRequest, HighlightResult, SemanticPack } from "@nsh/core";
import { describe, expect, it } from "vitest";

import { composeVueGold } from "../packs/vue/labeling/embedded.js";
import { labelVue } from "../packs/vue/labeling/label.js";
import { createCompositeVuePack, EXPRESSION_PREFIX } from "../packs/vue/runtime/composite.js";

const manifest = { id: "vue", documentKinds: [{ id: "vue", extensions: [".vue"] }] };
describe("Vue neural region composition", () => {
  it("uses compiler leaves for omitted operators and preserves neutral JSX text", () => {
    const source =
      '<script lang="tsx">const visible = !route; const data = [...items]; export const Badge = () => <b>Plain text</b>;</script>';
    const gold = composeVueGold(source, labelVue({ source, documentKind: "vue" }));
    for (const operator of ["!", "..."])
      expect(
        gold.spans.some(
          (s) => s.tokenType === "operator" && source.slice(s.start, s.end) === operator,
        ),
      ).toBe(true);
    const start = source.indexOf("Plain text");
    expect(gold.spans.some((s) => s.start < start + 10 && s.end > start)).toBe(false);
  });
  it("routes only predicted languages and restores wrapped UTF-16 expressions", async () => {
    const source = "🌌 abc def ghi jkl mno pqr stu data";
    const roles = ["javascript", "typescript", "jsx", "tsx", "css", "scss", "less"];
    const spans = roles.map((role, i) => ({
      start: 3 + i * 4,
      end: 6 + i * 4,
      tokenType: "embedded-" + role,
    }));
    spans.push({ start: 31, end: 35, tokenType: "embedded-expression" });
    const base: SemanticPack = {
      manifest,
      highlight: async () => ({ offsetEncoding: "utf-16", spans }),
    };
    const requests: HighlightRequest[] = [];
    const pack = createCompositeVuePack({
      base,
      highlightEmbedded: async (request) => {
        requests.push(request);
        const prefix = request.source.startsWith(EXPRESSION_PREFIX) ? EXPRESSION_PREFIX.length : 0;
        return {
          offsetEncoding: "utf-16",
          spans: [
            { start: prefix, end: request.source.length - (prefix ? 3 : 0), tokenType: "variable" },
          ],
        };
      },
    });
    const result = await pack.highlight({ source, documentKind: "vue" });
    expect(requests.map((r) => r.documentKind)).toEqual([...roles, "typescript"]);
    expect(requests.at(-1)?.source).toBe(EXPRESSION_PREFIX + "data" + "\n);");
    expect(result.spans.at(-1)).toEqual({ start: 31, end: 35, tokenType: "variable" });
  });
  it("does not use source tags to override a neural decision or fetch external sources", async () => {
    let calls = 0;
    const source = '<script src="https://example.invalid/x.ts">x</script>';
    const base: SemanticPack = {
      manifest,
      highlight: async () => ({
        offsetEncoding: "utf-16",
        spans: [{ start: 0, end: source.length, tokenType: "text" }],
      }),
    };
    const pack = createCompositeVuePack({
      base,
      highlightEmbedded: async () => {
        calls++;
        throw new Error("Should not run");
      },
    });
    expect((await pack.highlight({ source, documentKind: "vue" })).spans[0]?.tokenType).toBe(
      "text",
    );
    expect(calls).toBe(0);
  });
  it("rejects overlapping or surrogate-splitting model offsets and propagates errors", async () => {
    const request = { source: "🌌x", documentKind: "vue" };
    const base = (result: HighlightResult): SemanticPack => ({
      manifest,
      highlight: async () => result,
    });
    for (const spans of [
      [{ start: 1, end: 2, tokenType: "text" }],
      [
        { start: 0, end: 3, tokenType: "text" },
        { start: 2, end: 3, tokenType: "text" },
      ],
    ]) {
      const p = createCompositeVuePack({
        base: base({ offsetEncoding: "utf-16", spans }),
        highlightEmbedded: async () => {
          throw new Error("unused");
        },
      });
      await expect(p.highlight(request)).rejects.toThrow();
    }
    const p = createCompositeVuePack({
      base: base({
        offsetEncoding: "utf-16",
        spans: [{ start: 0, end: 3, tokenType: "embedded-typescript" }],
      }),
      highlightEmbedded: async () => {
        throw new Error("child failed");
      },
    });
    await expect(p.highlight(request)).rejects.toThrow("child failed");
  });
  it("builds offline child-role references independently, including interpolation and SCSS", () => {
    const source =
      '<template>{{ user.name }}</template><script setup lang="ts">const user = {name:"Ada"};</script><style lang="scss">$gap:8px; .card { gap:$gap; }</style>';
    const result = composeVueGold(source, labelVue({ source, documentKind: "vue" }));
    expect(
      result.spans.some(
        (s) => s.tokenType === "property" && source.slice(s.start, s.end) === "name",
      ),
    ).toBe(true);
    expect(
      result.spans.some(
        (s) => s.tokenType === "variable" && source.slice(s.start, s.end) === "$gap",
      ),
    ).toBe(true);
  });
});
