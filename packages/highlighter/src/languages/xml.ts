import type { BrowserModel } from "@nsh/browser";

const model: BrowserModel = {
  id: "xml",
  manifest: {
    id: "xml",
    documentKinds: [
      {
        id: "xml",
        extensions: [
          ".xml",
          ".xsd",
          ".xsl",
          ".xslt",
          ".wsdl",
          ".rss",
          ".atom",
          ".plist",
          ".csproj",
          ".props",
          ".targets",
        ],
      },
      {
        id: "svg",
        extensions: [".svg"],
      },
    ],
  },
  sha256: "ba610342452ee3a11e30158fa59dd2178fbfef75e1b775c5ed6c3ba6fa80250b",
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
    ],
    modifiers: ["closing"],
  },
  modifierThreshold: 0.6,
  decoder: {},
  modelUrl: () => new URL("../models/xml.onnx", import.meta.url).href,
};
export default model;
