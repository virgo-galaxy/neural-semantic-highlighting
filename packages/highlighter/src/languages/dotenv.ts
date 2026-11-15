import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "dotenv",
  manifest: {
    id: "dotenv",
    documentKinds: [
      {
        id: "dotenv",
        extensions: [
          ".env",
          ".dotenv",
          ".env.example",
          ".env.sample",
          ".env.template",
          ".env.local",
          ".env.development",
          ".env.production",
          ".env.test",
          ".env.staging",
          ".env.development.local",
          ".env.production.local",
        ],
      },
    ],
  },
  sha256: "763236a14024797f2beef5281593a725a5986a868e8c9b59b58cd1cd0fc48c4c",
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
  modelUrl: () => new URL("../models/dotenv.onnx", import.meta.url).href,
};
export default model;
