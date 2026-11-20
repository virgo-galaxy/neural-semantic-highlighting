import type { BrowserModel } from "@nsh/browser";

import css from "./css.js";
import typescript from "./typescript.js";

const model: BrowserModel = {
  id: "html",
  manifest: {
    id: "html",
    documentKinds: [
      {
        id: "html",
        extensions: [".html", ".htm"],
      },
    ],
  },
  sha256: "f3da38afbf1f52497720ec9dca0f2da810bc991c443d1167cf838700c22fb18d",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "punctuation",
      "tag",
      "attribute",
      "text",
      "entity",
      "embedded-javascript",
      "embedded-css",
      "embedded-data",
    ],
    modifiers: ["closing"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: ["embedded-javascript", "embedded-css", "embedded-data"],
    modifierRoles: {
      closing: ["tag"],
    },
  },
  modelUrl: () => new URL("../models/html.onnx", import.meta.url).href,
  dependencies: [typescript, css],
};
export default model;
