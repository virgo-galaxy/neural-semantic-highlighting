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
  sha256: "b796bb32dcfeeff7160ec42eac43f0a7f9450304675e12fb8869d52debcb05dc",
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
  modelUrl: () =>
    new URL(
      "../assets/v1/diff/b796bb32dcfeeff7160ec42eac43f0a7f9450304675e12fb8869d52debcb05dc.onnx",
      import.meta.url,
    ).href,
};
export default model;
