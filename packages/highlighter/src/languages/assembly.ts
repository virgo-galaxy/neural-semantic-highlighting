import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "assembly",
  manifest: {
    id: "assembly",
    documentKinds: [
      {
        id: "assembly",
        extensions: [".asm", ".ASM", ".nasm", ".masm", ".s", ".S", ".inc"],
      },
    ],
  },
  sha256: "820fa29c4a9db217c410108c3b35db5a2d42b47984e062dccf63ba87130f9a40",
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
      "function",
      "parameter",
      "variable",
    ],
    modifiers: ["declaration", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: ["comment"],
    modifierRoles: {
      declaration: ["function", "variable"],
      "default-library": ["variable"],
    },
  },
  modelUrl: () => new URL("../models/assembly.onnx", import.meta.url).href,
};
export default model;
