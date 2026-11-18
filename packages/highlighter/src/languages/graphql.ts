import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "graphql",
  manifest: {
    id: "graphql",
    documentKinds: [
      {
        id: "graphql",
        extensions: [".graphql", ".gql"],
      },
    ],
  },
  sha256: "fb2d44e56dbdae169a50cc9aa4d2908e730b275714e6a3eac033b792da856f49",
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
    modifiers: ["declaration", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: ["string", "comment"],
    modifierRoles: {
      declaration: [
        "type",
        "enum",
        "enum-member",
        "property",
        "parameter",
        "function",
        "label",
        "decorator",
      ],
      "default-library": ["type"],
    },
  },
  modelUrl: () => new URL("../models/graphql.onnx", import.meta.url).href,
};
export default model;
