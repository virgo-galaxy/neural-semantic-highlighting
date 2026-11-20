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
  sha256: "3dcdc12202c3f397c811128ca65a093e809e8bf44ef3e63386fe6448ea085c6f",
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
  modelUrl: () =>
    new URL(
      "../assets/v1/dotenv/3dcdc12202c3f397c811128ca65a093e809e8bf44ef3e63386fe6448ea085c6f.onnx",
      import.meta.url,
    ).href,
};
export default model;
