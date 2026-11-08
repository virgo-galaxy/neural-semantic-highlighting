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
  sha256: "93b924619a25dd853ad28b6f142587fc6f6bb5319cfc6464d9261bb808710cf9",
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
