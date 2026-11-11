import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "scala",
  manifest: {
    id: "scala",
    documentKinds: [
      {
        id: "scala",
        extensions: [".scala", ".sc", ".sbt"],
      },
    ],
  },
  sha256: "365f16bd6c55e0fa8a18607764e397a4d6bc0b70be96129311d776411c388647",
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
      "enum",
      "enum-member",
      "function",
      "method",
      "constructor",
      "parameter",
      "variable",
      "property",
      "type-parameter",
      "decorator",
      "constant",
      "label",
    ],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/scala.onnx", import.meta.url).href,
};
export default model;
