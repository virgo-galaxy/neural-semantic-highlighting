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
  sha256: "0f38eea262588ed4127b3121dd76652698040a42e4082f2b6a2a00d3f28b60f6",
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
  modelUrl: () => new URL("../models/c.onnx", import.meta.url).href,
};
export default model;
