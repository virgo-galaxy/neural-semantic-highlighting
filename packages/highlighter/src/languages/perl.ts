import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "perl",
  manifest: {
    id: "perl",
    documentKinds: [
      {
        id: "perl",
        extensions: [".pl", ".pm", ".t", ".perl"],
      },
    ],
  },
  sha256: "cbad629b7dee9e58d815a29ef59be1ef2ca9b3288f52082330e66a95a7dea2dd",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "number",
      "regexp",
      "operator",
      "punctuation",
      "namespace",
      "function",
      "method",
      "parameter",
      "variable",
      "property",
      "label",
    ],
    modifiers: ["declaration", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {
    modifierRoles: {
      declaration: ["variable", "function", "namespace", "parameter", "label"],
      "default-library": ["function"],
    },
  },
  modelUrl: () => new URL("../models/perl.onnx", import.meta.url).href,
};
export default model;
