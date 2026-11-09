import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "java",
  manifest: {
    id: "java",
    documentKinds: [
      {
        id: "java",
        extensions: [".java"],
      },
    ],
  },
  sha256: "2956a7876814e709ee93a3bae26544bb5c853828d40b0df382af0e4b2e9d50a8",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "number",
      "operator",
      "punctuation",
      "namespace",
      "type",
      "class",
      "interface",
      "enum",
      "enum-member",
      "constructor",
      "method",
      "parameter",
      "variable",
      "property",
      "decorator",
    ],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/java.onnx", import.meta.url).href,
};
export default model;
