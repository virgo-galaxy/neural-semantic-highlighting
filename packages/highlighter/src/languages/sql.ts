import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "sql",
  manifest: {
    id: "sql",
    documentKinds: [
      {
        id: "sql",
        extensions: [".sql", ".psql", ".pgsql", ".plsql"],
      },
    ],
  },
  sha256: "2c14ab1ed319eaf23e05af5708a306795afd10e4252e879e12eb6a780729dde7",
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
      "function",
      "parameter",
      "variable",
      "property",
    ],
    modifiers: ["declaration", "default-library"],
  },
  modifierThreshold: 0.6,
  decoder: {
    coalesceAdjacentTokenTypes: ["comment"],
    modifierRoles: {
      declaration: ["namespace", "function", "variable", "parameter"],
      "default-library": ["function"],
    },
  },
  modelUrl: () => new URL("../models/sql.onnx", import.meta.url).href,
};
export default model;
