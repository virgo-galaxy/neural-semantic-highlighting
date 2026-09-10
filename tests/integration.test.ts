import { createHighlighter, type SemanticPack } from "@nsh/core";
import { renderToHtml } from "@nsh/html";
import { describe, expect, it } from "vitest";

const pack: SemanticPack = {
  manifest: {
    id: "test-pack",
    documentKinds: [
      {
        id: "typescript",
        extensions: [".ts"],
      },
    ],
  },

  async highlight() {
    return {
      offsetEncoding: "utf-16",
      spans: [
        {
          start: 0,
          end: 5,
          tokenType: "keyword",
        },
        {
          start: 6,
          end: 11,
          tokenType: "variable",
          modifiers: ["declaration"],
        },
      ],
    };
  },
};

describe("highlighter integration", () => {
  it("highlights source and renders semantic HTML", async () => {
    const source = "const value = 1;";

    const highlighter = createHighlighter({
      packs: [pack],
    });

    const result = await highlighter.highlight({
      source,
      documentKind: "typescript",
    });

    const html = renderToHtml({
      source,
      documentKind: "typescript",
      result,
    });

    expect(html).toBe(
      '<pre class="nsh" data-language="typescript"><code>' +
        '<span class="nsh-token" data-token-type="keyword">const</span> ' +
        '<span class="nsh-token" data-token-type="variable" data-modifiers="declaration">value</span>' +
        " = 1;</code></pre>",
    );
  });
});
