import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "diff",
  manifest: {
    id: "diff",
    documentKinds: [
      {
        id: "diff",
        extensions: [".diff", ".patch"],
      },
    ],
  },
  sha256: "bedd7949793d33b6c8625706bfe1556e6ed95ee01b764f2f98dfe7ec1689b2ea",
  contextBytes: 512,
  schema: {
    tokenTypes: ["addition", "deletion", "heading", "label", "comment", "text", "punctuation"],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: [
      "addition",
      "deletion",
      "heading",
      "label",
      "comment",
      "text",
      "punctuation",
    ],
  },
  modelUrl: () => new URL("../models/diff.onnx", import.meta.url).href,
};
export default model;
