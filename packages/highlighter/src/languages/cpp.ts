import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "cpp",
  manifest: {
    id: "cpp",
    documentKinds: [
      {
        id: "cpp",
        extensions: [
          ".cpp",
          ".cc",
          ".cxx",
          ".c++",
          ".C",
          ".hpp",
          ".hh",
          ".hxx",
          ".h++",
          ".ipp",
          ".tpp",
        ],
      },
    ],
  },
  sha256: "c4bf80ec01700967279423c72315977d829841903481f712870317bf5dbdb890",
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
      "enum",
      "enum-member",
      "function",
      "constructor",
      "parameter",
      "type-parameter",
      "variable",
      "property",
      "label",
      "decorator",
    ],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/cpp.onnx", import.meta.url).href,
};
export default model;
