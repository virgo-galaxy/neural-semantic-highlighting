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
  sha256: "966e75ac022a90ee3cf4b177ffcf0e7ce85b23775ee8d8d485af0d526ad17913",
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
  modelUrl: () =>
    new URL(
      "../assets/v1/graphql/966e75ac022a90ee3cf4b177ffcf0e7ce85b23775ee8d8d485af0d526ad17913.onnx",
      import.meta.url,
    ).href,
};
export default model;
