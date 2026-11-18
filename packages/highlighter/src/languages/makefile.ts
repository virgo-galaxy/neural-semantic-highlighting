import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "makefile",
  manifest: {
    id: "makefile",
    documentKinds: [
      {
        id: "makefile",
        extensions: ["Makefile", "makefile", "GNUmakefile", ".mk", ".mak"],
      },
    ],
  },
  sha256: "0281ad6e304099ab5e24ed3f60860c9e6f0ea257e7abf941047c420636c39ebd",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "number",
      "operator",
      "punctuation",
      "function",
      "variable",
      "parameter",
      "label",
    ],
    modifiers: ["declaration", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: ["string"],
    modifierRoles: {
      declaration: ["variable", "label", "function"],
      "default-library": ["function"],
    },
  },
  modelUrl: () => new URL("../models/makefile.onnx", import.meta.url).href,
};
export default model;
