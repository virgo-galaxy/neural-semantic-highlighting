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
  sha256: "b39e066ce627bd289e2724e1530bc9d9c2b55f3024f8e7fe3625a0c7b4303eaa",
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
  modelUrl: () =>
    new URL(
      "../assets/v1/vue/b39e066ce627bd289e2724e1530bc9d9c2b55f3024f8e7fe3625a0c7b4303eaa.onnx",
      import.meta.url,
    ).href,
  dependencies: [typescript, css],
};
export default model;
