import type { BrowserModel } from "@nsh/browser";

import html from "./html.js";

const model: BrowserModel = {
  id: "php",
  manifest: {
    id: "php",
    documentKinds: [
      {
        id: "php",
        extensions: [".php", ".phtml"],
      },
    ],
  },
  sha256: "3c551599315bb5a931c69746290daf2562e591885167eb368898455910b80760",
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
      "interface",
      "trait",
      "enum",
      "enum-member",
      "function",
      "constructor",
      "parameter",
      "variable",
      "property",
      "constant",
      "label",
      "decorator",
      "embedded-html",
    ],
    modifiers: ["declaration"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: ["string", "comment", "embedded-html"],
  },
  modelUrl: () => new URL("../models/php.onnx", import.meta.url).href,
  dependencies: [html],
};
export default model;
