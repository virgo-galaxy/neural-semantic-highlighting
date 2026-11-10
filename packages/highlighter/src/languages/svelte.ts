import type { BrowserModel } from "@nsh/browser";

import css from "./css.js";
import typescript from "./typescript.js";

const model: BrowserModel = {
  id: "svelte",
  manifest: {
    id: "svelte",
    documentKinds: [
      {
        id: "svelte",
        extensions: [".svelte"],
      },
    ],
  },
  sha256: "089f82810da21659fc1f1fa89531105983b5bad8ab413d90288cdb75e2feaf93",
  contextBytes: 512,
  schema: {
    tokenTypes: [
      "keyword",
      "comment",
      "string",
      "number",
      "operator",
      "punctuation",
      "tag",
      "attribute",
      "text",
      "entity",
      "variable",
      "embedded-javascript",
      "embedded-typescript",
      "embedded-css",
      "embedded-scss",
      "embedded-less",
      "embedded-expression",
      "embedded-data",
    ],
    modifiers: ["closing"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: [
      "embedded-javascript",
      "embedded-typescript",
      "embedded-css",
      "embedded-scss",
      "embedded-less",
      "embedded-expression",
      "embedded-data",
      "comment",
      "string",
      "text",
    ],
  },
  modelUrl: () => new URL("../models/svelte.onnx", import.meta.url).href,
  dependencies: [typescript, css],
};
export default model;
