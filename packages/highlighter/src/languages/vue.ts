import type { BrowserModel } from "@nsh/browser";

import css from "./css.js";
import typescript from "./typescript.js";

const model: BrowserModel = {
  id: "vue",
  manifest: {
    id: "vue",
    documentKinds: [
      {
        id: "vue",
        extensions: [".vue"],
      },
    ],
  },
  sha256: "dee5e28cbce42351c5c098a0665cc374e410c0d16c9fa555e37582843a6edcce",
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
      "embedded-typescript",
      "embedded-jsx",
      "embedded-tsx",
      "embedded-scss",
      "embedded-less",
      "embedded-expression",
    ],
    modifiers: ["closing"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: [
      "embedded-javascript",
      "embedded-css",
      "embedded-data",
      "embedded-typescript",
      "embedded-jsx",
      "embedded-tsx",
      "embedded-scss",
      "embedded-less",
      "embedded-expression",
    ],
    modifierRoles: {
      closing: ["tag"],
    },
  },
  modelUrl: () => new URL("../models/vue.onnx", import.meta.url).href,
  dependencies: [typescript, css],
};
export default model;
