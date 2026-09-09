import { createHighlighter, renderToHtml } from "../dist/index.js";

const pack = {
  manifest: {
    id: "demo",
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
      ],
    };
  },
};

const source = "const value = 1;";

const highlighter = createHighlighter({
  packs: [pack],
});

const result = await highlighter.highlight({
  source,
  documentKind: "typescript",
});

document.querySelector("#app").innerHTML = renderToHtml({
  source,
  documentKind: "typescript",
  result,
});
