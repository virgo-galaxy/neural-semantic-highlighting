import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "ruby",
  manifest: {
    id: "ruby",
    documentKinds: [
      {
        id: "ruby",
        extensions: [".rb", ".rake", ".gemspec", "Gemfile", "Rakefile"],
      },
    ],
  },
  sha256: "f918254527025d7959a009a6a02a9d016ffe04457efe607e66c14260486b5ca1",
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
  modelUrl: () => new URL("../models/ruby.onnx", import.meta.url).href,
};
export default model;
