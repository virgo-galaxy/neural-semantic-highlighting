import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "typescript",
  manifest: {
    id: "typescript",
    documentKinds: [
      {
        id: "javascript",
        extensions: [".js"],
      },
      {
        id: "javascript-esm",
        extensions: [".mjs"],
      },
      {
        id: "javascript-commonjs",
        extensions: [".cjs"],
      },
      {
        id: "jsx",
        extensions: [".jsx"],
      },
      {
        id: "typescript",
        extensions: [".ts"],
      },
      {
        id: "typescript-esm",
        extensions: [".mts"],
      },
      {
        id: "typescript-commonjs",
        extensions: [".cts"],
      },
      {
        id: "tsx",
        extensions: [".tsx"],
      },
      {
        id: "typescript-declaration",
        extensions: [".d.ts"],
      },
      {
        id: "typescript-esm-declaration",
        extensions: [".d.mts"],
      },
      {
        id: "typescript-commonjs-declaration",
        extensions: [".d.cts"],
      },
    ],
  },
  sha256: "9d067b497f970f343c2bb063fe70748dcf3d4c841c9baeb6f9ab68fb741ebb33",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "number",
      "regexp",
      "operator",
      "punctuation",
      "namespace",
      "type",
      "class",
      "interface",
      "enum",
      "enum-member",
      "type-parameter",
      "function",
      "method",
      "constructor",
      "parameter",
      "variable",
      "property",
      "label",
      "decorator",
      "tag",
      "attribute",
    ],
    modifiers: [
      "declaration",
      "readonly",
      "static",
      "async",
      "generator",
      "abstract",
      "deprecated",
      "public",
      "protected",
      "private",
      "optional",
      "getter",
      "setter",
      "default-library",
    ],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () =>
    new URL(
      "../assets/v1/typescript/9d067b497f970f343c2bb063fe70748dcf3d4c841c9baeb6f9ab68fb741ebb33.onnx",
      import.meta.url,
    ).href,
};
export default model;
