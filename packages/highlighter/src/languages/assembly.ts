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
  sha256: "366d770f40ec20bcb97ed83d78c1a11f8a001a182efa0a5f31c69e03d04f6ad6",
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
