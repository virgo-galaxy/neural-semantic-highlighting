import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "ini",
  manifest: {
    id: "ini",
    documentKinds: [
      {
        id: "ini",
        extensions: [".ini", ".INI", ".cfg", ".CFG", ".editorconfig"],
      },
    ],
  },
  sha256: "307285b20477bd5bd71d2fdcb36b426040afe6120b8b6028d230c70af3308be1",
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
  modelUrl: () => new URL("../models/ini.onnx", import.meta.url).href,
};
export default model;
