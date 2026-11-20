import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "c",
  manifest: {
    id: "c",
    documentKinds: [
      {
        id: "c",
        extensions: [".c", ".h"],
      },
    ],
  },
  sha256: "6a599c8809d88458e626312753ee8844d81a71882404afd367ea6f464abfc68c",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "number",
      "operator",
      "punctuation",
      "type",
      "enum",
      "enum-member",
      "function",
      "parameter",
      "variable",
      "property",
      "label",
      "decorator",
    ],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  inferenceWindowing: {
    format: "nsh-overlap-logits-v1",
    strideBytes: 128,
    edgeWeightCap: 128,
    adaptiveWeight: 0.5,
  },
  modelUrl: () =>
    new URL(
      "../assets/v1/c/6a599c8809d88458e626312753ee8844d81a71882404afd367ea6f464abfc68c.onnx",
      import.meta.url,
    ).href,
};
export default model;
