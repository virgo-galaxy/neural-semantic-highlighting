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
  sha256: "37db79af3dafc762509698c8822837814c3bcb0bb96d1aa019053c17f72ceab8",
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
  modelUrl: () => new URL("../models/typescript.onnx", import.meta.url).href,
};
export default model;
